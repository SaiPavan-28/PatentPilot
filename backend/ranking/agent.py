"""
Ranking Agent — merges results from all retrieval sources, deduplicates,
applies the four-component hybrid score, and returns top-N ranked patents.
"""
from typing import List, Optional
import logging
from backend.ranking.fingerprint import compute_fingerprint, tanimoto_similarity
from backend.ranking.scorer import (
    fuzzy_string_match, compute_overlap_score,
    compute_confidence_score, generate_evidence_flags,
    compute_semantic_similarity_batch, compute_patent_recency
)
from backend.utils.logging import log_pipeline_stage

logger = logging.getLogger("patentpilot.ranking.agent")


def merge_and_deduplicate(patent_lists: List[List[dict]]) -> List[dict]:
    """
    Merge patent results from multiple sources, deduplicating by patent_number.
    Preserves all fields; last source wins for duplicates.
    """
    seen = {}
    for patent_list in patent_lists:
        for patent in patent_list:
            key = patent.get("patent_number", "").strip().upper()
            if key and key not in seen:
                seen[key] = patent
            elif key in seen:
                # Merge: fill in missing fields from the duplicate
                for field, value in patent.items():
                    if not seen[key].get(field) and value:
                        seen[key][field] = value
    return list(seen.values())


def rank_patents(
    patents: List[dict],
    query_smiles: str,
    target: Optional[str],
    indication: Optional[str],
    top_n: int = 25,
    semantic_scores: Optional[dict] = None  # patent_number -> semantic_score
) -> List[dict]:
    """
    Ranking Agent: score each patent with the four-component formula, sort, return top-N.
    
    Input:  merged, deduplicated patent list + molecule context
    Output: ranked list with full score breakdown
    """
    log_pipeline_stage(logger, "RANKING", {
        "message": f"Ranking {len(patents)} candidate patents",
        "query_smiles": query_smiles,
        "target": target,
        "indication": indication,
    })

    query_fp = compute_fingerprint(query_smiles)
    
    # Pre-compute TF-IDF semantic scores for the batch
    query_context = " ".join(filter(None, [target, indication]))
    patent_docs = [p.get("title", "") + " " + p.get("abstract", "") for p in patents]
    patent_numbers = [p.get("patent_number", "") for p in patents]
    tf_idf_semantic_scores = compute_semantic_similarity_batch(query_context, patent_docs, patent_numbers)

    ranked = []

    for patent in patents:
        patent_smiles = patent.get("smiles") or patent.get("compound_smiles", "")
        patent_number = patent.get("patent_number", "")

        # Component 1: Chemical similarity
        if patent_smiles and query_fp is not None:
            patent_fp = compute_fingerprint(patent_smiles)
            chem_sim = tanimoto_similarity(query_fp, patent_fp)
        else:
            chem_sim = patent.get("chemical_similarity", 0.0)

        # Component 2: Target match (fuzzy)
        patent_text = " ".join(filter(None, [
            patent.get("title", ""),
            patent.get("abstract", ""),
            patent.get("claims", "")
        ]))
        target_score = fuzzy_string_match(target, patent_text)

        # Component 3: Disease/indication match (fuzzy)
        disease_score = fuzzy_string_match(indication, patent_text)

        # Component 4: Semantic relevance (from LLM pre-scoring or TF-IDF fallback)
        semantic_score = 0.0
        if semantic_scores and patent_number in semantic_scores:
            semantic_score = semantic_scores[patent_number]
        elif patent_number in tf_idf_semantic_scores:
            semantic_score = tf_idf_semantic_scores[patent_number]

        # Component 5: Patent Recency
        recency_score = compute_patent_recency(patent.get("publication_date", ""))

        # Compute overall score
        overall = compute_overlap_score(chem_sim, target_score, disease_score, semantic_score, recency_score)

        # Confidence score
        confidence = compute_confidence_score(patent, bool(target), bool(indication))

        # Evidence flags
        flags = generate_evidence_flags(chem_sim, target_score, disease_score, patent, target, indication)

        ranked.append({
            **patent,
            "chemical_similarity": round(chem_sim, 4),
            "target_match": round(target_score, 4),
            "disease_match": round(disease_score, 4),
            "semantic_relevance": round(semantic_score, 4),
            "overall_score": overall,
            "confidence_score": confidence,
            "evidence_flags": flags,
        })

    # Sort by overall score descending, then confidence
    ranked.sort(key=lambda p: (p["overall_score"], p["confidence_score"]), reverse=True)

    # Assign ranks
    for i, p in enumerate(ranked[:top_n]):
        p["rank"] = i + 1

    log_pipeline_stage(logger, "RANKING_COMPLETE", {
        "message": f"Returning top {min(top_n, len(ranked))} patents",
        "top_score": ranked[0]["overall_score"] if ranked else 0
    })

    return ranked[:top_n]
