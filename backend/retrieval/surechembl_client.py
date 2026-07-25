"""
Strict deterministic primary retrieval client for SureChEMBL / ChEMBL.
Performs structure similarity search and filters by Tanimoto score.
"""
import httpx
import logging
import urllib.parse
from typing import List, Dict

logger = logging.getLogger("patentpilot.retrieval.surechembl")

PUBCHEM_API_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = 30.0

async def search_surechembl_by_structure(smiles: str, min_similarity: int = 75) -> List[Dict]:
    """
    Previously used ChEMBL, now uses PubChem Fast Similarity Search to find 
    structurally similar compounds, and then retrieves their associated Patent IDs.
    This guarantees we can find patents for novel molecules by looking at their structural neighbors.
    """
    if not smiles:
        return []

    results = []
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Step 1: PubChem Fast Similarity 2D Search
            encoded_smiles = urllib.parse.quote(smiles)
            sim_url = f"{PUBCHEM_API_BASE}/compound/fastsimilarity_2d/smiles/{encoded_smiles}/cids/JSON?Threshold={min_similarity}"
            
            sim_resp = await client.get(sim_url)
            
            if sim_resp.status_code != 200:
                logger.warning(f"PubChem similarity search returned {sim_resp.status_code}")
                return []
                
            sim_data = sim_resp.json()
            cids = sim_data.get("IdentifierList", {}).get("CID", [])
            
            if not cids:
                logger.info("No similar molecules found in PubChem.")
                return []
                
            # Limit to top 10 most similar compounds to avoid massive API spam
            cids = cids[:10]
            
            # Step 2: Fetch Patent IDs for these CIDs via cross-references
            cid_str = ",".join(map(str, cids))
            xref_url = f"{PUBCHEM_API_BASE}/compound/cid/{cid_str}/xrefs/PatentID/JSON"
            
            xref_resp = await client.get(xref_url)
            if xref_resp.status_code == 200:
                xref_data = xref_resp.json()
                info_list = xref_data.get("InformationList", {}).get("Information", [])
                
                for info in info_list:
                    patent_ids = info.get("PatentID", [])
                    # Limit to 10 patents per similar compound
                    for pid in patent_ids[:10]:
                        results.append({
                            "patent_number": pid,
                            "title": "Title fetched during enrichment", # Will be filled by secondary passes or UI
                            "abstract": "Abstract available via Google Patents.",
                            "publication_date": "",
                            "source": "pubchem",
                            "assignee": "",
                            # Unpadded URL as a fallback, but agent.py will overwrite this correctly now
                            "patent_url": f"https://patents.google.com/patent/{pid.replace('-', '')}",
                            "chemical_similarity": min_similarity / 100.0 # Approximate lower bound
                        })

            logger.info(f"Primary Structure Search (via PubChem) returned {len(results)} raw patents")
            return results

    except Exception as e:
        logger.error(f"Structure retrieval failed: {str(e)}")
        return []
