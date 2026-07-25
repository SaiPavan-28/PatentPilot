"""
Report generation endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from backend.db.database import get_db
from backend.db.models import Analysis, PatentResult, Report
from backend.models.schemas import ReportGenerateRequest, ReportResponse
from backend.ai.report_agent import generate_report
from backend.utils.exceptions import AnalysisNotFoundError
from backend.utils.logging import log_pipeline_stage

logger = logging.getLogger("patentpilot.api.report")
router = APIRouter()


@router.post("/report/generate", response_model=ReportResponse, tags=["Report"])
async def generate_patentability_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a structured patentability report for a completed analysis.
    Calls the Report Agent + Recommendation Agent.
    """
    analysis = db.query(Analysis).filter(Analysis.id == request.analysis_id).first()
    if not analysis:
        raise AnalysisNotFoundError(request.analysis_id)

    if analysis.status == "processing":
        raise HTTPException(status_code=409, detail="Analysis is still processing. Please wait.")
    if analysis.status == "error":
        raise HTTPException(status_code=422, detail="Analysis failed. Please resubmit.")

    patents = db.query(PatentResult).filter(
        PatentResult.analysis_id == request.analysis_id
    ).order_by(PatentResult.rank).all()

    patent_dicts = [
        {
            "patent_number": p.patent_number,
            "title": p.title,
            "abstract": p.abstract,
            "assignee": p.assignee,
            "publication_date": p.publication_date,
            "source": p.source,
            "chemical_similarity": p.chemical_similarity or 0.0,
            "target_match": p.target_match or 0.0,
            "disease_match": p.disease_match or 0.0,
            "semantic_relevance": p.semantic_relevance or 0.0,
            "overall_score": p.overall_score or 0.0,
            "confidence_score": p.confidence_score or 0.0,
            "evidence_flags": p.evidence_flags or [],
            "explanation": p.explanation,
        }
        for p in patents
    ]

    log_pipeline_stage(logger, "REPORT_REQUEST", {
        "message": f"Generating report for analysis {request.analysis_id}",
        "patent_count": len(patents),
    })

    try:
        report_data = await generate_report(
            analysis_id=request.analysis_id,
            smiles=analysis.smiles,
            target=analysis.target,
            indication=analysis.indication,
            ranked_patents=patent_dicts,
        )

        # Check if report already exists
        existing_report = db.query(Report).filter(Report.analysis_id == request.analysis_id).first()
        if existing_report:
            for key, value in report_data.items():
                if hasattr(existing_report, key):
                    setattr(existing_report, key, value)
            report = existing_report
        else:
            import uuid
            report = Report(
                id=str(uuid.uuid4()),
                analysis_id=request.analysis_id,
                **{k: v for k, v in report_data.items() if hasattr(Report, k)}
            )
            db.add(report)

        db.commit()
        db.refresh(report)
    except Exception as e:
        import traceback
        with open("report_error.txt", "w") as f:
            f.write(traceback.format_exc())
        logger.error(f"Failed to save report to database: {e}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to generate and save report")

    return ReportResponse(
        id=report.id,
        analysis_id=report.analysis_id,
        executive_summary=report.executive_summary,
        key_similar_patents=report.key_similar_patents or [],
        novelty_concerns=report.novelty_concerns or [],
        patents_requiring_review=report.patents_requiring_review or [],
        potential_novel_regions=report.potential_novel_regions,
        recommended_next_actions=report.recommended_next_actions or [],
        manual_review_checklist=report.manual_review_checklist or [],
        key_evidence=report.key_evidence or [],
        recommendation=report.recommendation,
        risk_score=report.risk_score,
        confidence_score=report.confidence_score,
        recommendation_rationale=report.recommendation_rationale,
        scoring_methodology_explanation=report.scoring_methodology_explanation,
        generated_at=report.generated_at,
    )


@router.get("/report/{analysis_id}", response_model=ReportResponse, tags=["Report"])
async def get_report(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve an existing report for an analysis."""
    report = db.query(Report).filter(Report.analysis_id == analysis_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found. Please generate it first.")
    return ReportResponse(
        id=report.id,
        analysis_id=report.analysis_id,
        executive_summary=report.executive_summary,
        key_similar_patents=report.key_similar_patents or [],
        novelty_concerns=report.novelty_concerns or [],
        patents_requiring_review=report.patents_requiring_review or [],
        potential_novel_regions=report.potential_novel_regions,
        recommended_next_actions=report.recommended_next_actions or [],
        manual_review_checklist=report.manual_review_checklist or [],
        key_evidence=report.key_evidence or [],
        recommendation=report.recommendation,
        risk_score=report.risk_score,
        confidence_score=report.confidence_score,
        recommendation_rationale=report.recommendation_rationale,
        scoring_methodology_explanation=report.scoring_methodology_explanation,
        generated_at=report.generated_at,
    )
