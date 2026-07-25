"""
Explanation Agent — generates grounded per-patent explanations.
Each explanation is anchored to the actual retrieved patent data + scores.
Never generic. Never hallucinated.
"""
import json
import logging
from typing import Optional

from backend.ai.llm_client import call_llm
from backend.utils.logging import log_pipeline_stage
from backend.utils.exceptions import LLMError

logger = logging.getLogger("patentpilot.ai.explanation_agent")

SYSTEM_PROMPT = """You are a patent analysis expert assistant for PatentPilot, an AI-assisted Freedom-to-Operate screening tool.

Your role is to generate grounded, specific explanations for why a patent is relevant to a submitted molecule.

CRITICAL RULES:
- You are prohibited from inventing patent metadata.
- Only explain the supplied information.
- If information is missing, state 'Information unavailable'.
- Your explanation MUST reference specific information from the patent title, abstract, and claims provided.
- DO NOT generate generic or templated text. Every sentence must be traceable to the actual data provided.
- Use the exact similarity scores provided to calibrate your confidence language.
- Be concise, precise, and scientifically accurate.
- Format your response as valid JSON matching the exact schema requested.
- This is a SCREENING tool — always note uncertainty and recommend expert review for high-risk findings.
"""


async def generate_patent_explanation(
    patent: dict,
    molecule_smiles: str,
    molecule_target: Optional[str],
    molecule_indication: Optional[str],
) -> dict:
    """
    Explanation Agent: Generate a grounded, per-patent explanation.
    
    Input:  One patent's fields + its four sub-scores
    Output: Structured explanation object
    """
    patent_number = patent.get("patent_number", "Unknown")
    log_pipeline_stage(logger, "EXPLANATION", {
        "message": f"Generating explanation for {patent_number}",
        "overall_score": patent.get("overall_score", 0),
    })

    # Build the grounded prompt with actual data
    user_prompt = f"""Generate a grounded patent relevance explanation for the following:

## Submitted Molecule
- SMILES: {molecule_smiles}
- Target (if provided): {molecule_target or 'Not specified'}
- Disease/Indication (if provided): {molecule_indication or 'Not specified'}

## Patent Data (use ONLY this information — do not fabricate details)
- Patent Number: {patent.get('patent_number', 'Unknown')}
- Title: {patent.get('title', 'Not available')}
- Assignee: {patent.get('assignee', 'Not available')}
- Publication Date: {patent.get('publication_date', 'Not available')}
- Abstract: {patent.get('abstract', 'Not available')[:1500]}
- Claims (if available): {(patent.get('claims', '') or '')[:500]}

## Computed Similarity Scores (factual — use these to calibrate confidence)
- Chemical Structural Similarity (Tanimoto): {patent.get('chemical_similarity', 0):.1%}
- Target Keyword Match: {patent.get('target_match', 0):.1%}
- Disease/Indication Match: {patent.get('disease_match', 0):.1%}
- Overall Overlap Score: {patent.get('overall_score', 0):.1%}
- Assessment Confidence: {patent.get('confidence_score', 0):.1%}
- Evidence Flags: {', '.join(patent.get('evidence_flags', [])) or 'None'}

## Task
Generate a JSON object with EXACTLY these four fields. Every sentence must reference specific data above:

{{
  "why_retrieved": "1-2 sentences explaining why this patent was retrieved (cite specific score values and patent fields)",
  "similar_regions": "2-3 sentences describing which structural/functional/therapeutic aspects appear similar (cite title/abstract/scores)",
  "possible_novelty_overlap": "2-3 sentences describing the specific overlap risk (cite claims, abstract text, or score thresholds)",
  "confidence": "1-2 sentences on assessment confidence and key uncertainty factors (cite data completeness and score levels)",
  "risk_level": "Strictly one of: Low Risk, Medium Risk, High Risk"
}}

Return ONLY the JSON object. No markdown, no preamble."""

    try:
        raw_response = await call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=600,
            temperature=0.2,
        )

        # Parse JSON response
        clean = raw_response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        explanation = json.loads(clean.strip())

        # Validate required fields
        required = ["why_retrieved", "similar_regions", "possible_novelty_overlap", "confidence", "risk_level"]
        for field in required:
            if field not in explanation:
                explanation[field] = f"Analysis for {patent_number} — see scores above."

        # Add key concerns based on scores
        key_concerns = []
        if patent.get("overall_score", 0) >= 0.75:
            key_concerns.append(f"HIGH OVERLAP: Score {patent['overall_score']:.2f} exceeds 0.75 threshold")
        if patent.get("chemical_similarity", 0) >= 0.6:
            key_concerns.append(f"Significant structural similarity ({patent['chemical_similarity']:.1%})")
        if patent.get("target_match", 0) >= 0.7:
            key_concerns.append("High target keyword match — same therapeutic mechanism likely")

        explanation["key_concerns"] = key_concerns
        return explanation

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse LLM JSON for {patent_number}: {e}")
        return _fallback_explanation(patent, molecule_target, molecule_indication)
    except LLMError as e:
        logger.error(f"LLM error for {patent_number}: {e}")
        return _fallback_explanation(patent, molecule_target, molecule_indication)


def _fallback_explanation(patent: dict, target: Optional[str], indication: Optional[str]) -> dict:
    """Rule-based fallback explanation when LLM is unavailable."""
    score = patent.get("overall_score", 0)
    chem = patent.get("chemical_similarity", 0)
    return {
        "why_retrieved": (
            f"Patent {patent.get('patent_number')} was retrieved with an overall overlap score of "
            f"{score:.1%}. Chemical structural similarity: {chem:.1%}."
        ),
        "similar_regions": (
            f"{'High structural similarity detected. ' if chem >= 0.6 else ''}"
            f"{'Target keyword match: ' + target if target and patent.get('target_match', 0) > 0.3 else ''}"
            f"{'Indication match: ' + indication if indication and patent.get('disease_match', 0) > 0.3 else ''}"
        ).strip() or "Similarity detected via hybrid text and structural analysis.",
        "possible_novelty_overlap": (
            f"Overlap score of {score:.1%} {'exceeds' if score >= 0.75 else 'approaches'} the "
            f"high-risk threshold (0.75). {'Manual expert review strongly recommended.' if score >= 0.6 else 'Monitor closely.'}"
        ),
        "confidence": (
            f"Assessment confidence: {patent.get('confidence_score', 0):.1%}. "
            f"{'Abstract available — moderate evidence quality.' if patent.get('abstract') else 'No abstract — limited evidence.'}"
        ),
        "risk_level": "High Risk" if score >= 0.75 else "Medium Risk" if score >= 0.40 else "Low Risk",
        "key_concerns": [],
    }
