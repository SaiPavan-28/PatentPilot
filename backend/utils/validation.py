"""
RDKit SMILES validation and 2D structure generation.
"""
from typing import Optional, Tuple
import logging

logger = logging.getLogger("patentpilot.validation")


def validate_smiles(smiles: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate a SMILES string using RDKit.
    Returns: (is_valid, canonical_smiles, error_message)
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return False, None, "RDKit could not parse this SMILES string. Please check the syntax."
        canonical = Chem.MolToSmiles(mol)
        return True, canonical, None
    except ImportError:
        # Graceful fallback if RDKit is not installed
        logger.warning("RDKit not available, using basic SMILES validation")
        return _basic_smiles_validation(smiles)
    except Exception as e:
        return False, None, f"Validation error: {str(e)}"


def _basic_smiles_validation(smiles: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Basic SMILES validation without RDKit."""
    s = smiles.strip()
    if not s:
        return False, None, "SMILES string is empty"
    if len(s) < 1:
        return False, None, "SMILES string is too short"
    # Basic bracket balance check
    if s.count("(") != s.count(")"):
        return False, None, "Unbalanced parentheses in SMILES"
    if s.count("[") != s.count("]"):
        return False, None, "Unbalanced brackets in SMILES"
    return True, s, None


def get_molecule_properties(smiles: str) -> dict:
    """Get molecular properties using RDKit."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors
        from rdkit.Chem.rdMolDescriptors import GetMorganFingerprintAsBitVect
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return {}
        return {
            "molecular_formula": rdMolDescriptors.CalcMolFormula(mol),
            "molecular_weight": round(Descriptors.MolWt(mol), 2),
            "exact_mass": round(Descriptors.ExactMolWt(mol), 4),
            "num_atoms": mol.GetNumAtoms(),
            "num_heavy_atoms": mol.GetNumHeavyAtoms(),
            "num_rings": rdMolDescriptors.CalcNumRings(mol),
            "inchi": Chem.MolToInchi(mol),
            "inchikey": Chem.MolToInchiKey(mol),
            "morgan_ecfp4": list(GetMorganFingerprintAsBitVect(mol, 2, nBits=2048).GetOnBits()),
        }
    except ImportError:
        return {}
    except Exception as e:
        logger.error(f"Error getting molecule properties: {e}")
        return {}


def generate_structure_svg(smiles: str) -> Optional[str]:
    """Generate a 2D structure SVG from SMILES using RDKit."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Draw
        from rdkit.Chem.Draw import rdMolDraw2D

        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return None

        # Compute 2D coordinates
        from rdkit.Chem import AllChem
        AllChem.Compute2DCoords(mol)

        drawer = rdMolDraw2D.MolDraw2DSVG(400, 300)
        drawer.drawOptions().addStereoAnnotation = True
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        return svg
    except ImportError:
        logger.warning("RDKit not available, cannot generate SVG")
        return _generate_placeholder_svg(smiles)
    except Exception as e:
        logger.error(f"SVG generation error: {e}")
        return _generate_placeholder_svg(smiles)


def _generate_placeholder_svg(smiles: str) -> str:
    """Fetch 2D structure from PubChem when RDKit is unavailable."""
    import urllib.request
    import urllib.parse
    import base64
    try:
        encoded_smiles = urllib.parse.quote(smiles)
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{encoded_smiles}/PNG"
        req = urllib.request.Request(url, headers={'User-Agent': 'PatentPilot/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            png_data = response.read()
            b64_img = base64.b64encode(png_data).decode('utf-8')
            
            return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#ffffff" rx="12"/>
  <image href="data:image/png;base64,{b64_img}" x="50" y="0" width="300" height="300"/>
</svg>'''
    except Exception as e:
        logger.error(f"Failed to fetch PubChem image: {e}")
        truncated = smiles[:30] + "..." if len(smiles) > 30 else smiles
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#f8fafc" rx="12"/>
  <text x="200" y="150" text-anchor="middle" fill="#64748b" font-size="14" font-family="monospace">{truncated}</text>
</svg>'''
