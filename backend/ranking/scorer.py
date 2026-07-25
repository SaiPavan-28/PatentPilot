"""
Five-component hybrid scoring formula for patent relevance.
overall_score = 0.40*chemical + 0.25*target + 0.20*semantic + 0.10*disease + 0.05*recency
"""
from typing import Optional, List, Dict
import re
import logging

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger("patentpilot.ranking.scorer")


def fuzzy_string_match(query: Optional[str], text: Optional[str]) -> float:
    """
    Compute a simple string match score between a query and a text.
    Returns 0-1. Uses partial substring matching + token overlap.
    """
    if not query or not text:
        return 0.0
    q = query.lower().strip()
    t = text.lower().strip()
    # Direct substring match
    if q in t:
        return 1.0
    # Token overlap (Jaccard-like)
    q_tokens = set(re.findall(r'\w+', q))
    t_tokens = set(re.findall(r'\w+', t))
    if not q_tokens:
        return 0.0
    intersection = q_tokens & t_tokens
    union = q_tokens | t_tokens
    jaccard = len(intersection) / len(union) if union else 0.0
    # Reward partial matches generously — this is a screening tool
    return min(1.0, jaccard * 1.5)


def compute_semantic_similarity_batch(
    query_text: str,
    patent_documents: List[str],
    patent_numbers: List[str]
) -> Dict[str, float]:
    """
    Compute TF-IDF cosine similarity between the query (target+indication)
    and a batch of patent documents (title+abstract).
    Returns a dictionary mapping patent_number to semantic_score (0.0 to 1.0).
    """
    if not query_text or not patent_documents or not SKLEARN_AVAILABLE:
        return {pn: 0.0 for pn in patent_numbers}

    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        
        # Fit on both query and documents to build vocabulary
        all_texts = [query_text] + patent_documents
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate cosine similarity of the query (index 0) against the rest
        cosine_sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        # Boost scores slightly to normalize them to the 0-1 scale expected by the formula
        return {pn: min(1.0, float(score) * 1.5) for pn, score in zip(patent_numbers, cosine_sims)}
    except Exception as e:
        logger.error(f"Semantic scoring failed: {e}")
        return {pn: 0.0 for pn in patent_numbers}


def compute_patent_recency(publication_date: str) -> float:
    """
    Calculate a recency score from 0-1 based on publication date.
    Newer patents get higher scores.
    """
    if not publication_date:
        return 0.0
    try:
        from datetime import datetime
        # Parse typical YYYY-MM-DD
        pub_year = int(publication_date[:4])
        current_year = datetime.now().year
        age = max(0, current_year - pub_year)
        
        # 0 years old = 1.0, 20 years old = 0.0
        score = max(0.0, 1.0 - (age / 20.0))
        return score
    except Exception:
        return 0.5


def compute_overlap_score(
    chemical_similarity: float,
    target_match: float,
    disease_match: float,
    semantic_relevance: float,
    patent_recency: float = 0.5,
    weights: dict = None
) -> float:
    """
    Compute weighted overlap score from five components.
    Default weights: chemical=0.40, target=0.25, semantic=0.20, disease=0.10, recency=0.05
    """
    if weights is None:
        weights = {
            "chemical": 0.40,
            "target": 0.25,
            "semantic": 0.20,
            "disease": 0.10,
            "recency": 0.05
        }
    score = (
        weights["chemical"] * chemical_similarity
        + weights["target"] * target_match
        + weights["semantic"] * semantic_relevance
        + weights["disease"] * disease_match
        + weights["recency"] * patent_recency
    )
    return round(min(1.0, max(0.0, score)), 4)


def compute_confidence_score(
    patent_data: dict,
    target_provided: bool,
    indication_provided: bool
) -> float:
    """
    Data-completeness-based confidence score.
    Lower confidence if patent is missing fields or researcher didn't supply target/indication.
    """
    score = 1.0
    # Penalize missing data
    if not patent_data.get("abstract"):
        score -= 0.25
    if not patent_data.get("assignee"):
        score -= 0.05
    if not patent_data.get("publication_date"):
        score -= 0.05
    if not patent_data.get("claims"):
        score -= 0.10
    # Penalize for missing researcher inputs (means target/disease scores are 0)
    if not target_provided:
        score -= 0.15
    if not indication_provided:
        score -= 0.10
    return round(max(0.1, min(1.0, score)), 4)


def generate_evidence_flags(
    chemical_similarity: float,
    target_match: float,
    disease_match: float,
    patent_data: dict,
    molecule_target: Optional[str],
    molecule_indication: Optional[str]
) -> List[str]:
    """Generate human-readable evidence flags for explainability."""
    flags = []
    if chemical_similarity >= 0.8:
        flags.append("✓ Very high structural similarity (≥80%)")
    elif chemical_similarity >= 0.6:
        flags.append("✓ Significant structural similarity (≥60%)")
    elif chemical_similarity >= 0.4:
        flags.append("⚠ Moderate structural similarity (≥40%)")
    elif chemical_similarity > 0:
        flags.append("○ Low structural similarity")

    if target_match >= 0.8:
        flags.append(f"✓ Same biological target ({molecule_target})")
    elif target_match >= 0.4:
        flags.append(f"⚠ Similar biological target")

    if disease_match >= 0.8:
        flags.append(f"✓ Same therapeutic indication ({molecule_indication})")
    elif disease_match >= 0.4:
        flags.append(f"⚠ Related therapeutic indication")

    abstract = patent_data.get("abstract", "") or ""
    if "derivative" in abstract.lower() or "analog" in abstract.lower():
        flags.append("⚠ Claims may cover similar derivatives/analogs")
    if "composition" in abstract.lower():
        flags.append("○ Composition-of-matter claim detected")

    return flags


def determine_risk_level(patents: list) -> tuple:
    """
    Apply risk thresholds to determine overall recommendation.
    Returns: (risk_label, risk_score, rationale)
    """
    if not patents:
        return "Low Risk", 0.0, "No relevant patents found in the search."

    scores = [p.get("overall_score", 0) for p in patents]
    max_score = max(scores) if scores else 0.0
    avg_score = sum(scores) / len(scores) if scores else 0.0

    if max_score >= 0.75:
        risk = "High Risk"
        rationale = (
            f"At least one patent has an overlap score ≥0.75 (max={max_score:.2f}), "
            "indicating substantial structural/functional similarity. "
            "Immediate expert review is strongly recommended."
        )
    elif max_score >= 0.40:
        risk = "Medium Risk"
        rationale = (
            f"Patents with overlap scores between 0.40–0.75 (max={max_score:.2f}, avg={avg_score:.2f}) "
            "indicate moderate similarity that warrants professional patent attorney review "
            "before proceeding with development."
        )
    else:
        risk = "Low Risk"
        rationale = (
            f"All retrieved patents have overlap scores <0.40 (max={max_score:.2f}), "
            "suggesting low structural and functional overlap. "
            "Standard patent monitoring recommended as a precaution."
        )

    return risk, round(max_score, 4), rationale
