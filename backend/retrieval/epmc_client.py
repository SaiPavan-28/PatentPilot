"""
Europe PMC API client.
Used as the secondary semantic search engine for patents when PatentsView is unreachable.
"""
import httpx
import asyncio
import logging
import urllib.parse
from typing import List, Dict

logger = logging.getLogger("patentpilot.retrieval.epmc")

EPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TIMEOUT = 20.0
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
            logger.warning(f"EPMC request failed (attempt {attempt+1}/{MAX_RETRIES}): {e.__class__.__name__}. Retrying in {wait}s...")
            await asyncio.sleep(wait)
    raise last_exc


async def search_epmc_patents(query_terms: List[str], max_results: int = 50) -> List[Dict]:
    """
    Search Europe PMC for patent documents using semantic terms.
    Uses resultType=core to get full abstracts.
    Retries automatically on DNS/connection failures.
    """
    if not query_terms:
        return []

    # Cap at 5 terms to avoid URL bloat / query rejections
    terms_to_search = query_terms[:5]
    formatted_terms = " OR ".join([f'"{term.replace(chr(34), "")}"' for term in terms_to_search])
    query = f'SRC:PAT AND ({formatted_terms})'

    encoded_query = urllib.parse.quote(query)
    # Use resultType=core to get full abstracts
    url = f"{EPMC_BASE}?query={encoded_query}&format=json&resultType=core&cursorMark=*&pageSize={max_results}"

    results = []

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await _get_with_retry(client, url)
            if resp.status_code == 200:
                data = resp.json()
                results_list = data.get("resultList", {}).get("result", [])

                for doc in results_list:
                    patent_id = doc.get("id", "")
                    if not patent_id:
                        continue

                    # core result type provides abstractText for patents
                    abstract = doc.get("abstractText", "") or ""
                    
                    results.append({
                        "patent_number": patent_id,
                        "title": doc.get("title", "") or "",
                        "abstract": abstract,
                        "publication_date": doc.get("firstPublicationDate", "") or "",
                        "source": "europe_pmc",
                        "assignee": doc.get("authorString", "") or "",
                        "patent_url": f"https://patents.google.com/patent/{patent_id.replace('-', '')}"
                    })

                logger.info(f"Europe PMC returned {len(results)} patents for batch query.")
                return results
            else:
                logger.warning(f"Europe PMC returned {resp.status_code}")
                return []
    except Exception as e:
        logger.warning(f"Europe PMC search failed after retries ({e.__class__.__name__})")
        return []
