"""
Strict deterministic primary retrieval client for SureChEMBL / ChEMBL.
Performs structure similarity search and filters by Tanimoto score.
"""
import httpx
import logging
import urllib.parse
from typing import List, Dict

logger = logging.getLogger("patentpilot.retrieval.surechembl")

CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"
TIMEOUT = 15.0

async def search_surechembl_by_structure(smiles: str, min_similarity: int = 75) -> List[Dict]:
    """
    Search ChEMBL API by structure similarity.
    Retrieves patents for molecules with Tanimoto similarity >= min_similarity.
    """
    if not smiles:
        return []

    results = []
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Step 1: Similarity Search
            encoded_smiles = urllib.parse.quote(smiles)
            mol_url = f"{CHEMBL_API_BASE}/similarity/{encoded_smiles}/{min_similarity}.json"
            mol_resp = await client.get(mol_url)
            
            if mol_resp.status_code != 200:
                logger.warning(f"ChEMBL similarity search returned {mol_resp.status_code}")
                return []
                
            mol_data = mol_resp.json()
            molecules = mol_data.get("molecules", [])
            
            # Map chembl_id to similarity score
            mol_sim_map = {}
            for m in molecules:
                cid = m.get("molecule_chembl_id")
                sim = float(m.get("similarity", 0.0))
                # Ensure it meets threshold strictly (API occasionally returns slightly lower due to internal differences)
                if cid and sim >= (min_similarity / 100.0):
                    mol_sim_map[cid] = sim
            
            if not mol_sim_map:
                logger.info("No molecules met similarity threshold in SureChEMBL")
                return []

            # Step 2 & 3: Find documents for these molecules
            # We'll batch to avoid massive API calls
            for chembl_id, sim_score in list(mol_sim_map.items())[:10]:
                act_url = f"{CHEMBL_API_BASE}/activity.json?molecule_chembl_id={chembl_id}&limit=20"
                act_resp = await client.get(act_url)
                if act_resp.status_code != 200:
                    continue
                    
                activities = act_resp.json().get("activities", [])
                doc_ids = set([act.get("document_chembl_id") for act in activities if act.get("document_chembl_id")])
                
                for doc_id in list(doc_ids)[:5]: # Limit docs per molecule
                    doc_url = f"{CHEMBL_API_BASE}/document.json?document_chembl_id={doc_id}"
                    doc_resp = await client.get(doc_url)
                    if doc_resp.status_code == 200:
                        docs = doc_resp.json().get("documents", [])
                        if docs:
                            doc = docs[0]
                            if doc.get("document_type") == "Patent":
                                patent_id = doc.get("patent_id")
                                if patent_id:
                                    results.append({
                                        "patent_number": patent_id,
                                        "title": doc.get("title", ""),
                                        "abstract": doc.get("abstract", ""),
                                        "publication_date": str(doc.get("year", "")),
                                        "source": "surechembl",
                                        "assignee": "",
                                        "patent_url": f"https://patents.google.com/patent/{patent_id.replace('-', '')}",
                                        "chemical_similarity": sim_score # Seed with retrieved exact similarity
                                    })

            logger.info(f"Primary Structure Search returned {len(results)} verified patents")
            return results

    except Exception as e:
        logger.error(f"SureChEMBL structure retrieval failed: {str(e)}")
        return []
