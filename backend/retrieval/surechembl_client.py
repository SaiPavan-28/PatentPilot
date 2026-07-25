"""
Strict deterministic primary retrieval client.
Uses PubChem Fast Similarity Search to find structurally related patents.
"""
import httpx
import asyncio
import logging
import urllib.parse
from typing import List, Dict

logger = logging.getLogger("patentpilot.retrieval.surechembl")

PUBCHEM_API_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = 45.0
MAX_RETRIES = 3
RETRY_DELAY = 2.0


async def _get_with_retry(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """GET with exponential backoff retries for DNS/connection failures."""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return await client.get(url)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            last_exc = e
            wait = RETRY_DELAY * (attempt + 1)
            logger.warning(f"Request failed (attempt {attempt+1}/{MAX_RETRIES}): {e.__class__.__name__}. Retrying in {wait}s...")
            await asyncio.sleep(wait)
    raise last_exc


async def search_surechembl_by_structure(smiles: str, min_similarity: int = 75) -> List[Dict]:
    """
    Uses PubChem Fast Similarity Search to find structurally similar compounds,
    then retrieves their associated Patent IDs via cross-references.
    Retries automatically on DNS/connection failures.
    """
    if not smiles:
        return []

    results = []

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Step 1: PubChem Fast Similarity 2D Search
            encoded_smiles = urllib.parse.quote(smiles)
            sim_url = f"{PUBCHEM_API_BASE}/compound/fastsimilarity_2d/smiles/{encoded_smiles}/cids/JSON?Threshold={min_similarity}"

            sim_resp = await _get_with_retry(client, sim_url)

            if sim_resp.status_code == 400:
                # PubChem rejected the SMILES — try exact match instead
                logger.warning(f"PubChem similarity search rejected SMILES (400). Trying exact match.")
                exact_url = f"{PUBCHEM_API_BASE}/compound/smiles/{encoded_smiles}/cids/JSON"
                sim_resp = await _get_with_retry(client, exact_url)

            if sim_resp.status_code != 200:
                logger.warning(f"PubChem search returned {sim_resp.status_code}")
                return []

            sim_data = sim_resp.json()
            cids = sim_data.get("IdentifierList", {}).get("CID", [])

            if not cids:
                logger.info("No similar molecules found in PubChem.")
                return []

            # Limit to top 10 to avoid API spam
            cids = cids[:10]

            # Step 2: Fetch Patent IDs for these CIDs via cross-references
            cid_str = ",".join(map(str, cids))
            xref_url = f"{PUBCHEM_API_BASE}/compound/cid/{cid_str}/xrefs/PatentID/JSON"

            xref_resp = await _get_with_retry(client, xref_url)
            if xref_resp.status_code == 200:
                xref_data = xref_resp.json()
                info_list = xref_data.get("InformationList", {}).get("Information", [])

                for info in info_list:
                    patent_ids = info.get("PatentID", [])
                    for pid in patent_ids[:10]:
                        results.append({
                            "patent_number": pid,
                            "title": "",
                            "abstract": "",
                            "publication_date": "",
                            "source": "pubchem",
                            "assignee": "",
                            "patent_url": f"https://patents.google.com/patent/{pid.replace('-', '')}",
                            "chemical_similarity": min_similarity / 100.0
                        })

            logger.info(f"Primary Structure Search (via PubChem) returned {len(results)} raw patents")
            return results

    except Exception as e:
        logger.error(f"Structure retrieval failed after retries: {e.__class__.__name__}: {str(e)}")
        return []
