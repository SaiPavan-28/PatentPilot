"""
RDKit fingerprinting + Tanimoto similarity for the Ranking Agent.
"""
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger("patentpilot.ranking.fingerprint")


def compute_fingerprint(smiles: str):
    """Compute Morgan/ECFP4 fingerprint for a SMILES string."""
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
    except ImportError:
        logger.warning("RDKit not available — chemical similarity will be 0")
        return None
    except Exception as e:
        logger.error(f"Fingerprint error: {e}")
        return None


def tanimoto_similarity(fp1, fp2) -> float:
    """Compute Tanimoto (Jaccard) similarity between two fingerprints."""
    if fp1 is None or fp2 is None:
        return 0.0
    try:
        from rdkit import DataStructs
        return float(DataStructs.TanimotoSimilarity(fp1, fp2))
    except Exception as e:
        logger.error(f"Tanimoto error: {e}")
        return 0.0


def smiles_to_smiles_similarity(smiles1: str, smiles2: str) -> float:
    """Compute Tanimoto similarity between two SMILES strings."""
    fp1 = compute_fingerprint(smiles1)
    fp2 = compute_fingerprint(smiles2)
    return tanimoto_similarity(fp1, fp2)
