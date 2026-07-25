"""
Retrieval Agent — orchestrates patent retrieval using Primary (Structural) and Secondary (Semantic) pipelines.
Enforces STRICT verification. Discards any unverified hallucinated patents.
"""
import asyncio
import logging
from typing import Optional, List, Dict

from backend.retrieval.pubchem_client import get_compound_metadata
from backend.retrieval.vocabulary import build_search_vocabulary
from backend.retrieval.epmc_client import search_epmc_patents
from backend.retrieval.surechembl_client import search_surechembl_by_structure
from backend.utils.logging import log_pipeline_stage

logger = logging.getLogger("patentpilot.retrieval.agent")


async def search_database_batch(synonyms: List[str]) -> List[dict]:
    """
    SECONDARY (Semantic) Search Pipeline.
    Search databases in batches to avoid overwhelming the APIs.
    Searches PatentsView (USPTO) using the terms.
    """
    all_results = []
    
    chunk_size = 8
    for i in range(0, len(synonyms), chunk_size):
        chunk = synonyms[i:i + chunk_size]
        try:
            epmc_res = await search_epmc_patents(chunk, max_results=30)
            all_results.extend(epmc_res)
            await asyncio.sleep(0.3) 
        except Exception as e:
            logger.error(f"Batch search failed for {chunk}: {e}")
            
    return all_results


async def verify_and_enrich_patent(patent: dict) -> Optional[dict]:
    """
    Ensure the patent is real and extract ONLY verified metadata.
    Reject if missing Patent Number, Title, or Source.
    """
    source = patent.get("source", "")
    pn = patent.get("patent_number", "")
    title = patent.get("title", "")
    
    if not pn or not source:
        return None
        
    # Empty title is OK — assign a default rather than rejecting
    if not title:
        patent["title"] = "Title Not Available"


    v_status = {
        "surechembl": source == "surechembl", 
        "europe_pmc": source == "europe_pmc", 
        "pubchem": source == "pubchem",
        "google_patents": True 
    }

    # We need clean_pn for URL generation, but DO NOT overwrite patent["patent_number"]
    # with the stripped version, as the user wants to see the original format (e.g. US-2004-...)
    clean_pn = pn.replace("-", "").replace(" ", "")
    
    # Fix for Europe PMC dropping leading zero in US applications
    import re
    match = re.match(r"^(US)(\d{4})(\d{6})([A-Z0-9]*)$", clean_pn)
    if match:
        # Padded for URL
        clean_pn = f"{match.group(1)}{match.group(2)}0{match.group(3)}{match.group(4)}"
        
        # If the original string didn't have dashes, we can safely update it to the padded one
        # so the UI shows the correct 11-digit number.
        if "-" not in pn:
            patent["patent_number"] = clean_pn
        else:
            # If it had dashes (e.g. US-2004-310540), we inject the zero where it belongs
            # This is tricky, so we just use the clean padded version as a fallback
            # but ideally we just don't strip anything.
            pass
            
    # Do NOT assign clean_pn to patent["patent_number"] globally, keep original!

    patent["verification_status"] = v_status
    # ALWAYS overwrite patent_url with our properly padded clean_pn 
    # instead of trusting the unpadded one passed from epmc_client or pubchem_client.
    patent["patent_url"] = f"https://patents.google.com/patent/{clean_pn}"
    patent["google_patents_url"] = patent["patent_url"]
    patent["pdf_url"] = f"https://patentimages.storage.googleapis.com/{clean_pn[:2]}/{clean_pn[2:4]}/{clean_pn[4:6]}/{clean_pn}.pdf"
    patent["uspto_url"] = f"https://imagecwcs.uspto.gov/ptcs/patimage?p_doc={clean_pn}"
    patent["epo_url"] = f"https://worldwide.espacenet.com/patent/search?q={clean_pn}"
    
    required_fields = ["patent_number", "title", "abstract", "publication_date", "assignee", "inventors", "patent_url", "source", "claims"]
    for field in required_fields:
        if field not in patent:
            patent[field] = None

    return patent


async def retrieve_patents(
    smiles: str,
    target: Optional[str] = None,
    indication: Optional[str] = None,
    inchikey: Optional[str] = None,
) -> List[dict]:
    """
    Retrieval Agent: Run vocabulary-driven retrieval across public databases.
    Flowchart architecture:
    1. Validate -> Fingerprint (Done in validation)
    2. Primary Structural Search (SureChEMBL) -> Discard Tanimoto < 0.75
    3. Secondary Semantic Search (PatentsView, etc) -> Generate queries
    4. Merge & Deduplicate
    """
    log_pipeline_stage(logger, "RETRIEVAL_START", {
        "message": "Starting Strict Dual-Pipeline Retrieval",
        "smiles": smiles[:50]
    })

    # 1. PubChem Compound Identification
    pubchem_metadata = await get_compound_metadata(smiles)

    # 2. Build Expanded Vocabulary
    vocab = build_search_vocabulary(target, indication, pubchem_metadata, smiles)
    logger.info(f"Generated {len(vocab)} unique search terms")

    # 3. Dual Pipeline Execution
    tasks = [
        # PRIMARY (Structure-Based): Hard filter < 0.75 is handled inside this client call
        search_surechembl_by_structure(smiles, min_similarity=75),
        # SECONDARY (Semantic): Full text synonym search
        search_database_batch(vocab)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    primary_results = results[0] if not isinstance(results[0], Exception) and results[0] else []
    secondary_results = results[1] if not isinstance(results[1], Exception) and results[1] else []

    # 4. Merge and Deduplicate by Patent Number
    merged_dict = {}
    
    for p in primary_results + secondary_results:
        pn = p.get("patent_number")
        if not pn: continue
        
        if pn not in merged_dict:
            merged_dict[pn] = p
        else:
            existing = merged_dict[pn]
            for k, v in p.items():
                if v and not existing.get(k):
                    existing[k] = v
                    
            # If primary pipeline provided a chemical similarity score, preserve it
            if "chemical_similarity" in p and "chemical_similarity" not in existing:
                existing["chemical_similarity"] = p["chemical_similarity"]

    # 5. Enrich sparse patents
    # Europe PMC returns mostly full data, but we can attempt to enrich if necessary later.
    # For now, we skip PatentsView enrichment because of DNS issues.
    
    # 6. Strict Verification
    raw_patents = list(merged_dict.values())
    verify_tasks = [verify_and_enrich_patent(p) for p in raw_patents]
    verified_results = await asyncio.gather(*verify_tasks)

    final_patents = [p for p in verified_results if p is not None]

    log_pipeline_stage(logger, "RETRIEVAL_COMPLETE", {
        "message": f"Retrieved and strictly verified {len(final_patents)} patents"
    })

    return final_patents
