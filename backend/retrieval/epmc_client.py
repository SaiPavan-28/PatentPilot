"""
Europe PMC API client.
Used as the secondary semantic search engine for patents when PatentsView is unreachable.
"""
import httpx
import logging
import urllib.parse
from typing import List, Dict

logger = logging.getLogger("patentpilot.retrieval.epmc")

EPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TIMEOUT = 10.0

async def search_epmc_patents(query_terms: List[str], max_results: int = 50) -> List[Dict]:
    """
    Search Europe PMC for patent documents using semantic terms.
    """
    if not query_terms:
        return []

    # Join terms with OR and wrap in quotes
    # E.g., SRC:PAT AND ("term1" OR "term2")
    formatted_terms = " OR ".join([f'"{term.replace(chr(34), "")}"' for term in query_terms])
    query = f'SRC:PAT AND ({formatted_terms})'
    
    encoded_query = urllib.parse.quote(query)
    url = f"{EPMC_BASE}?query={encoded_query}&format=json&resultType=lite&cursorMark=*&pageSize={max_results}"
    
    results = []
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                results_list = data.get("resultList", {}).get("result", [])
                
                for doc in results_list:
                    patent_id = doc.get("id", "")
                    # Europe PMC patent IDs often look like "US20120123456"
                    if not patent_id:
                        continue
                        
                    results.append({
                        "patent_number": patent_id,
                        "title": doc.get("title", ""),
                        "abstract": doc.get("abstractText", ""), # Europe PMC lite might not always have abstract
                        "publication_date": doc.get("firstPublicationDate", ""),
                        "source": "europe_pmc",
                        "assignee": doc.get("authorString", ""), # Sometimes assignee is in authorString
                        "patent_url": f"https://patents.google.com/patent/{patent_id.replace('-', '')}"
                    })
                    
                logger.info(f"Europe PMC returned {len(results)} patents for batch query.")
                return results
            else:
                logger.warning(f"Europe PMC returned {resp.status_code}")
                return []
    except Exception as e:
        logger.warning(f"Europe PMC search failed ({e.__class__.__name__})")
        return []
