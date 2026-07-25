"""
Report Agent — assembles the full structured patentability report.
Recommendation Agent — applies scoring thresholds to produce the final risk label.
Both are implemented here as they share data and are sequentially dependent.
"""
import json
import logging
from typing import List, Optional

from backend.ai.llm_client import call_llm
from backend.ranking.scorer import determine_risk_level
from backend.utils.logging import log_pipeline_stage
from backend.utils.exceptions import LLMError

logger = logging.getLogger("patentpilot.ai.report_agent")


REPORT_SYSTEM_PROMPT = """You are a senior patent analyst generating a structured Freedom-to-Operate (FTO) screening report for PatentPilot.

CRITICAL RULES:
- Base ALL conclusions on the actual patent data and scores provided. Never invent details.
- Use precise language. Cite specific patent numbers, scores, and text.
- Include the mandatory legal disclaimer that this is a SCREENING TOOL, not legal advice.
- Return ONLY valid JSON matching the exact schema requested.
- Be analytical and evidence-based, not generic.
"""


async def generate_report(
    analysis_id: str,
    smiles: str,
    target: Optional[str],
    indication: Optional[str],
    ranked_patents: List[dict],
) -> dict:
    """
    Report Agent + Recommendation Agent:
    Assemble the full patentability report from all ranked patents.
    
    Input:  All ranked patents with explanations + molecule context
    Output: Structured report dict
    """
    log_pipeline_stage(logger, "REPORT_GENERATION", {
        "message": f"Generating report for analysis {analysis_id}",
        "patent_count": len(ranked_patents),
    })

    # ── Recommendation Agent: apply thresholds ─────────────────────────────────
    patent_dicts = [
        {"patent_number": p.get("patent_number"), "overall_score": p.get("overall_score", 0)}
        for p in ranked_patents
    ]
    risk_label, risk_score, risk_rationale = determine_risk_level(patent_dicts)

    # ── Identify key patents for report ────────────────────────────────────────
    high_risk_patents = [p for p in ranked_patents if p.get("overall_score", 0) >= 0.75]
    review_patents = [p for p in ranked_patents if 0.40 <= p.get("overall_score", 0) < 0.75]
    key_patents = sorted(ranked_patents, key=lambda p: p.get("overall_score", 0), reverse=True)[:5]

    # ── Build LLM prompt with real data ───────────────────────────────────────
    patent_summaries = []
    for i, p in enumerate(ranked_patents[:8], 1):
        exp = p.get("explanation", {}) or {}
        patent_summaries.append(
            f"{i}. [{p.get('patent_number')}] Score: {p.get('overall_score', 0):.2f} | "
            f"Title: {(p.get('title') or 'N/A')[:100]} | "
            f"Assignee: {p.get('assignee', 'N/A')} | "
            f"Date: {p.get('publication_date', 'N/A')} | "
            f"Chem Sim: {p.get('chemical_similarity', 0):.2f} | "
            f"Target: {p.get('target_match', 0):.2f} | Disease: {p.get('disease_match', 0):.2f}"
        )

    user_prompt = f"""Generate a Freedom-to-Operate screening report for:

## Molecule Under Analysis
- SMILES: {smiles}
- Target: {target or 'Not specified'}
- Disease/Indication: {indication or 'Not specified'}
- Analysis ID: {analysis_id}

## Risk Assessment (already computed — use these exact values):
- Overall Recommendation: {risk_label}
- Risk Score: {risk_score:.4f}
- Rationale: {risk_rationale}

## Top Retrieved Patents (ranked by overlap score):
{chr(10).join(patent_summaries)}

## Key Statistics:
- Total patents analyzed: {len(ranked_patents)}
- High-risk patents (score ≥0.75): {len(high_risk_patents)}
- Requires-review patents (0.40-0.75): {len(review_patents)}
- Low-overlap patents (<0.40): {len(ranked_patents) - len(high_risk_patents) - len(review_patents)}

Generate a JSON object with EXACTLY these fields:

{{
  "Executive Summary": "3-4 paragraph summary: molecule analyzed, retrieval approach, key findings, and recommendation. Must cite specific patent numbers and scores. Include FTO screening disclaimer.",
  "Key Similar Patents": [
    {{
      "patent_number": "...",
      "title": "...",
      "overall_score": 0.0,
      "key_concern": "one sentence on the specific overlap concern"
    }}
  ],
  "Potential Novelty Concerns": ["list of 3-5 specific novelty concerns, each citing a patent number or score"],
  "Patents needing manual review": ["list of patent numbers needing manual review"],
  "Overall Recommendation": "Strictly one of: Low Risk, Medium Risk, High Risk"
}}

Return ONLY the JSON object. No markdown, no preamble."""

    try:
        raw = await call_llm(
            system_prompt=REPORT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=2500,
            temperature=0.2,
        )

        clean = raw.strip()
        
        # Robustly extract JSON block if wrapped in markdown
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean, re.DOTALL)
        if json_match:
            clean = json_match.group(1)
            
        report_data = json.loads(clean.strip())

    except (json.JSONDecodeError, LLMError) as e:
        logger.error(f"Report LLM failed: {e}, using rule-based fallback")
        report_data = _fallback_report(ranked_patents, target, indication)

    # ── Enrich with computed values ───────────────────────────────────────────
    confidences = [p.get("confidence_score", 0.5) for p in ranked_patents]
    
    # Map JSON to report_data dictionary keys used by database model
    mapped_data = {
        "executive_summary": report_data.get("Executive Summary", ""),
        "key_similar_patents": report_data.get("Key Similar Patents", []),
        "novelty_concerns": report_data.get("Potential Novelty Concerns", []),
        "patents_requiring_review": report_data.get("Patents needing manual review", []),
        "recommendation": report_data.get("Overall Recommendation", risk_label),
        "risk_score": round(risk_score, 4),
        "recommendation_rationale": risk_rationale,
        "confidence_score": round(sum(confidences) / len(confidences), 4) if confidences else 0.5,
    }

    # Ensure key_similar_patents has full data
    if not mapped_data.get("key_similar_patents"):
        mapped_data["key_similar_patents"] = [
            {
                "patent_number": p.get("patent_number"),
                "title": p.get("title", "N/A"),
                "overall_score": p.get("overall_score", 0),
                "key_concern": f"Overlap score: {p.get('overall_score', 0):.2f}"
            }
            for p in key_patents
        ]

    log_pipeline_stage(logger, "REPORT_COMPLETE", {
        "message": "Report generated successfully",
        "recommendation": risk_label,
        "risk_score": risk_score,
    })

    return mapped_data


def _fallback_report(patents: List[dict], target: Optional[str], indication: Optional[str]) -> dict:
    """Rule-based report when LLM is unavailable."""
    top_patents = sorted(patents, key=lambda p: p.get("overall_score", 0), reverse=True)[:3]
    high_risk = [p for p in patents if p.get("overall_score", 0) >= 0.75]

    return {
        "executive_summary": (
            f"PatentPilot FTO screening identified {len(patents)} relevant patents for the submitted molecule "
            f"(target: {target or 'unspecified'}, indication: {indication or 'unspecified'}). "
            f"{'High patent risk detected — ' + str(len(high_risk)) + ' patent(s) exceed the 0.75 overlap threshold.' if high_risk else 'No patents exceeded the high-risk threshold.'} "
            "This is a preliminary screening report and does not constitute legal advice. Consult a qualified patent attorney before making development decisions."
        ),
        "key_similar_patents": [
            {
                "patent_number": p.get("patent_number"),
                "title": p.get("title", "N/A"),
                "overall_score": p.get("overall_score", 0),
                "key_concern": f"Overlap score {p.get('overall_score', 0):.2f}"
            }
            for p in top_patents
        ],
        "novelty_concerns": [
            f"Patent {p.get('patent_number')} has overlap score {p.get('overall_score', 0):.2f}"
            for p in top_patents
        ],
        "potential_novel_regions": "Detailed novelty region analysis requires manual review of full patent claims.",
        "recommended_next_actions": [
            "Consult a registered patent attorney for full FTO opinion",
            "Review full claim text for each flagged patent",
            f"Consider structural modifications to reduce overlap with {top_patents[0].get('patent_number', 'key patents') if top_patents else 'flagged patents'}",
            "Run a comprehensive search including expired patents",
        ],
        "manual_review_checklist": [
            "Review independent claims of each flagged patent",
            "Check whether flagged patents are in-force or expired",
            "Verify geographic coverage of flagged patents",
            "Assess whether proposed molecule falls within claim scope",
            "Identify potential design-around opportunities",
        ],
        "key_evidence": [
            f"{p.get('patent_number')}: Overall score {p.get('overall_score', 0):.2f}"
            for p in top_patents
        ],
        "scoring_methodology_explanation": (
            "Overlap score computed as: 0.35×chemical_similarity + 0.25×target_match + "
            "0.20×disease_match + 0.20×semantic_relevance. "
            "Risk thresholds: ≥0.75 = High Risk; 0.40-0.75 = Requires Expert Review; <0.40 = Low Risk."
        ),
    }
