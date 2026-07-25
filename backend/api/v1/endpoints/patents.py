"""
Patents endpoints — list patents for an analysis, update review status, get explanation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from backend.db.database import get_db
from backend.db.models import Analysis, PatentResult, ReviewStatus
from backend.models.schemas import PatentResponse, ReviewStatusUpdate, ReviewStatusResponse, ScoreBreakdown
from backend.utils.exceptions import AnalysisNotFoundError

logger = logging.getLogger("patentpilot.api.patents")
router = APIRouter()


def _patent_to_response(patent: PatentResult) -> PatentResponse:
    """Convert DB model to response schema."""
    review_status = "unreviewed"
    if patent.review_status:
        review_status = patent.review_status.status

    return PatentResponse(
        id=patent.id,
        analysis_id=patent.analysis_id,
        patent_number=patent.patent_number,
        title=patent.title,
        abstract=patent.abstract,
        claims=patent.claims,
        assignee=patent.assignee,
        publication_date=patent.publication_date,
        source=patent.source,
        patent_url=patent.patent_url,
        scores=ScoreBreakdown(
            chemical_similarity=patent.chemical_similarity or 0.0,
            target_match=patent.target_match or 0.0,
            disease_match=patent.disease_match or 0.0,
            semantic_relevance=patent.semantic_relevance or 0.0,
            overall_score=patent.overall_score or 0.0,
            confidence_score=patent.confidence_score or 0.0,
            evidence_flags=patent.evidence_flags or [],
        ),
        explanation=patent.explanation,
        explanation_generated=patent.explanation_generated or False,
        rank=patent.rank or 0,
        review_status=review_status,
        created_at=patent.created_at,
    )


@router.get("/patents/{analysis_id}", tags=["Patents"])
async def list_patents(
    analysis_id: str,
    sort_by: Optional[str] = "overall_score",
    order: Optional[str] = "desc",
    source_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List all patents for an analysis, with optional filtering and sorting.
    """
    # Verify analysis exists
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise AnalysisNotFoundError(analysis_id)

    patents = db.query(PatentResult).filter(PatentResult.analysis_id == analysis_id).all()

    # Filter
    if source_filter:
        patents = [p for p in patents if p.source == source_filter]
    if status_filter:
        patents = [p for p in patents if p.review_status and p.review_status.status == status_filter]

    # Sort
    sort_key = {"overall_score": lambda p: p.overall_score or 0,
                "publication_date": lambda p: p.publication_date or "",
                "assignee": lambda p: p.assignee or "",
                "chemical_similarity": lambda p: p.chemical_similarity or 0}.get(
        sort_by, lambda p: p.overall_score or 0
    )
    patents.sort(key=sort_key, reverse=(order == "desc"))

    response = {
        "analysis_id": analysis_id,
        "analysis_status": analysis.status,
        "smiles": analysis.smiles,
        "molecule_name": analysis.molecule_name,
        "target": analysis.target,
        "indication": analysis.indication,
        "patent_count": len(patents),
        "patents": [_patent_to_response(p) for p in patents]
    }
    
    if not patents:
        response["message"] = "No verified patents were found in the queried public patent databases."
        
    return response


@router.put("/patents/{patent_id}/review", response_model=ReviewStatusResponse, tags=["Patents"])
async def update_review_status(
    patent_id: str,
    request: ReviewStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the review status for a patent (reviewed/flagged/dismissed)."""
    patent = db.query(PatentResult).filter(PatentResult.id == patent_id).first()
    if not patent:
        raise HTTPException(status_code=404, detail=f"Patent {patent_id} not found")

    review = db.query(ReviewStatus).filter(ReviewStatus.patent_id == patent_id).first()
    if review:
        review.status = request.status.value
        review.notes = request.notes
    else:
        review = ReviewStatus(
            analysis_id=patent.analysis_id,
            patent_id=patent_id,
            status=request.status.value,
            notes=request.notes,
        )
        db.add(review)

    db.commit()
    logger.info(f"Patent {patent_id} status updated to {request.status.value}")

    return ReviewStatusResponse(
        patent_id=patent_id,
        status=request.status.value,
        notes=request.notes,
    )


@router.get("/patents/{patent_id}/detail", tags=["Patents"])
async def get_patent_detail(patent_id: str, db: Session = Depends(get_db)):
    """Get full detail for a single patent including explanation."""
    patent = db.query(PatentResult).filter(PatentResult.id == patent_id).first()
    if not patent:
        raise HTTPException(status_code=404, detail="Patent not found")
    return _patent_to_response(patent)
