"""
PubChem PUG-REST API client.
Used STRICTLY for compound identification and synonym generation.
NO patent retrieval is performed here.
"""
import httpx
import logging
from typing import Optional, Dict

logger = logging.getLogger("patentpilot.retrieval.pubchem")

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = 15.0


async def get_compound_metadata(smiles: str) -> Dict:
    """
    Retrieve compound metadata from PubChem using exact SMILES match.
    Returns:
    {
        "cid": int,
        "iupac_name": str,
        "synonyms": list[str],
        "canonical_smiles": str,
        "inchikey": str,
        "molecular_formula": str
    }
    """
    if not smiles:
        return {}
        
    encoded_smiles = smiles.replace("/", ".").replace("+", "%2B")
    
    metadata = {
        "cid": None,
        "iupac_name": None,
        "synonyms": [],
        "canonical_smiles": None,
        "inchikey": None,
        "molecular_formula": None
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 1. Get properties
            prop_url = f"{PUBCHEM_BASE}/compound/smiles/{encoded_smiles}/property/IUPACName,MolecularFormula,CanonicalSMILES,InChIKey/JSON"
            prop_resp = await client.get(prop_url)
            
            if prop_resp.status_code == 200:
                data = prop_resp.json()
                props = data.get("PropertyTable", {}).get("Properties", [])
                if props:
                    p = props[0]
                    metadata["cid"] = p.get("CID")
                    metadata["iupac_name"] = p.get("IUPACName")
                    metadata["canonical_smiles"] = p.get("CanonicalSMILES")
                    metadata["inchikey"] = p.get("InChIKey")
                    metadata["molecular_formula"] = p.get("MolecularFormula")

            # 2. Get Synonyms
            syn_url = f"{PUBCHEM_BASE}/compound/smiles/{encoded_smiles}/synonyms/JSON"
            syn_resp = await client.get(syn_url)
            
            if syn_resp.status_code == 200:
                data = syn_resp.json()
                infos = data.get("InformationList", {}).get("Information", [])
                if infos:
                    # PubChem can return thousands of synonyms, keep top 100 for safety
                    metadata["synonyms"] = infos[0].get("Synonym", [])[:100]

            logger.info(f"PubChem metadata retrieved for {smiles[:20]}... (CID: {metadata['cid']}, Synonyms: {len(metadata['synonyms'])})")
            return metadata

    except Exception as e:
        logger.error(f"PubChem metadata retrieval error: {e}")
        return metadata
