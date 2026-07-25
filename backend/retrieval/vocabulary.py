"""
Search vocabulary builder for PatentPilot.
Aggregates and deduplicates synonyms from various sources for robust patent retrieval.
"""
from typing import List, Optional, Dict
import re

def build_search_vocabulary(
    target: Optional[str],
    indication: Optional[str],
    pubchem_metadata: Dict
) -> List[str]:
    """
    Build an expanded, deduplicated search vocabulary.
    Includes:
    - Official name / IUPAC name
    - PubChem synonyms
    - Common drug names & Trade names
    - CAS number
    - Target
    - Disease
    """
    vocab = set()
    
    # 1. Target & Indication
    if target:
        vocab.add(target.strip().lower())
    if indication:
        vocab.add(indication.strip().lower())
        
    # 2. PubChem Metadata
    if pubchem_metadata:
        iupac = pubchem_metadata.get("iupac_name")
        if iupac:
            vocab.add(iupac.strip().lower())
            
        synonyms = pubchem_metadata.get("synonyms", [])
        for syn in synonyms:
            syn = syn.strip().lower()
            # Filter out very long complex names that break search engines
            if len(syn) < 60:
                vocab.add(syn)
                
    # Basic filtering to remove pure structural identifiers that aren't good search terms
    # like raw SMILES or InChI strings if they somehow got in
    filtered_vocab = []
    for term in vocab:
        if not term:
            continue
        # Skip raw InChI
        if term.startswith("inchi="):
            continue
        filtered_vocab.append(term)
        
    # Sort for deterministic output (longest terms first often helps exact match strategies, 
    # but here we just sort alphabetically)
    return sorted(filtered_vocab)
