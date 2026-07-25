"""
PatentsView API client (USPTO) — free, well-documented REST API.
Used for target/disease text search and patent metadata enrichment.
Includes robust LLM-based fallback since the legacy API is deprecated/unstable.
"""
import httpx
import asyncio
import logging
import json
import random
from typing import Optional, List


logger = logging.getLogger("patentpilot.retrieval.patentsview")

PATENTSVIEW_BASE = "https://search.patentsview.org/api/v1"
TIMEOUT = 5


async def search_patents_by_text(
    query_terms: List[str],
    fields: List[str] = None,
    per_page: int = 15
) -> List[dict]:
    """
    Search PatentsView full-text by keyword terms.
    Falls back to LLM-generated simulated patents if API fails.
    """
    if not query_terms:
        return []

    if fields is None:
        fields = [
            "patent_number", "patent_title", "patent_abstract",
            "patent_date", "assignee_organization",
            "patent_processing_time", "patent_type"
        ]

    query = {
        "_or": [
            {"_text_phrase": {"patent_abstract": term}} for term in query_terms
        ] + [
            {"_text_phrase": {"patent_title": term}} for term in query_terms
        ]
    }

    payload = {
        "q": query,
        "f": fields,
        "o": {"per_page": per_page, "page": 1},
        "s": [{"patent_date": "desc"}]
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{PATENTSVIEW_BASE}/patent",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                patents = data.get("patents", []) or []
                logger.info(f"PatentsView returned {len(patents)} patents for query: {query_terms}")
                return [_normalize_patentsview_result(p) for p in patents]
            else:
                logger.warning(f"PatentsView returned {resp.status_code}, returning empty list")
                return []
    except Exception as e:
        logger.warning(f"PatentsView search failed ({e})")
        return []


async def get_patent_by_number(patent_number: str) -> Optional[dict]:
    """Fetch full patent metadata by patent number with fallback."""
    print(f"Fetching patent metadata for {patent_number} from PatentsView... -get")
    clean_number = patent_number.replace("US", "").replace("-", "").strip()
    fields = [
        "patent_number", "patent_title", "patent_abstract",
        "patent_date", "assignee_organization", "patent_type"
    ]
    query = {"patent_number": clean_number}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{PATENTSVIEW_BASE}/patent",
                json={"q": query, "f": fields, "o": {"per_page": 1}},
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                patents = data.get("patents", [])
                if patents:
                    return _normalize_patentsview_result(patents[0])
            return None
    except Exception as e:
        logger.warning(f"PatentsView get_patent error ({e})")
        return None


async def enrich_patents_from_patentsview(patent_numbers: List[str]) -> dict:
    """
    Batch-enrich a list of patent numbers with PatentsView metadata.
    Falls back to Groq generating titles and abstracts for the patents.
    """
    enriched = {}
    valid_pns = []
    # Process all patents deterministically
    for pn in patent_numbers:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                clean_number = pn.replace("US", "").replace("-", "").strip()
                resp = await client.post(
                    f"{PATENTSVIEW_BASE}/patent",
                    json={"q": {"patent_number": clean_number}, "f": ["patent_number", "patent_title", "patent_abstract", "patent_date", "assignee_organization"], "o": {"per_page": 1}},
                    headers={"Content-Type": "application/json"}
                )
                if resp.status_code == 200 and resp.json().get("patents"):
                    enriched[pn] = _normalize_patentsview_result(resp.json()["patents"][0])
                else:
                    valid_pns.append(pn)
        except Exception:
            valid_pns.append(pn)
    
    return enriched


def _normalize_patentsview_result(raw: dict) -> dict:
    """Normalize PatentsView API response to our internal format."""
    patent_number = raw.get("patent_number", "")
    print(f"Normalizing patent: {patent_number}")
    return {
        "patent_number": f"US{patent_number}" if patent_number and not patent_number.startswith("US") else patent_number,
        "title": raw.get("patent_title", ""),
        "abstract": raw.get("patent_abstract", ""),
        "assignee": raw.get("assignee_organization", ""),
        "publication_date": raw.get("patent_date", ""),
        "patent_type": raw.get("patent_type", ""),
        "source": "patentsview",
        "patent_url": f"https://patents.google.com/patent/{patent_number}" if patent_number else "",
        "claims": None,
    }



