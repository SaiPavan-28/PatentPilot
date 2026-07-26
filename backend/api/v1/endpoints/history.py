"""
History and Dashboard endpoints.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
import logging

from backend.db.database import get_db
from backend.db.models import Analysis, PatentResult, Report
from backend.models.schemas import HistoryListResponse, AnalysisSummary, DashboardStats, AnalysisDetailResponse
from backend.utils.exceptions import AnalysisNotFoundError
from backend.api.v1.endpoints.patents import _patent_to_response
from backend.models.schemas import ScoreBreakdown

logger = logging.getLogger("patentpilot.api.history")
router = APIRouter()


@router.get("/history", response_model=HistoryListResponse, tags=["History"])
async def list_analyses(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List all past analyses with pagination and search.
    """
    query = db.query(Analysis)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Analysis.smiles.ilike(search_term)) |
            (Analysis.molecule_name.ilike(search_term)) |
            (Analysis.target.ilike(search_term)) |
            (Analysis.indication.ilike(search_term))
        )
    if status:
        query = query.filter(Analysis.status == status)

    total = query.count()
    analyses = query.order_by(desc(Analysis.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for a in analyses:
        patent_count = db.query(func.count(PatentResult.id)).filter(PatentResult.analysis_id == a.id).scalar()
        report = db.query(Report).filter(Report.analysis_id == a.id).first()
        items.append(AnalysisSummary(
            id=a.id,
            smiles=a.smiles,
            molecule_name=a.molecule_name,
            target=a.target,
            indication=a.indication,
            status=a.status,
            patent_count=patent_count or 0,
            has_report=bool(report),
            risk_level=report.recommendation if report else None,
            risk_score=report.risk_score if report else None,
            created_at=a.created_at,
        ))

    return HistoryListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/history/{analysis_id}", response_model=AnalysisDetailResponse, tags=["History"])
async def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Get full detail of a past analysis including all patents and report."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise AnalysisNotFoundError(analysis_id)

    patents = db.query(PatentResult).filter(
        PatentResult.analysis_id == analysis_id
    ).order_by(PatentResult.rank).all()

    report = db.query(Report).filter(Report.analysis_id == analysis_id).first()
    report_data = None
    if report:
        from backend.models.schemas import ReportResponse
        report_data = ReportResponse(
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

    return AnalysisDetailResponse(
        id=analysis.id,
        smiles=analysis.smiles,
        molecule_name=analysis.molecule_name,
        target=analysis.target,
        indication=analysis.indication,
        status=analysis.status,
        structure_svg=analysis.structure_svg,
        patents=[_patent_to_response(p) for p in patents],
        report=report_data,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.delete("/history/{analysis_id}", tags=["History"])
async def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Delete an analysis and all its associated patents and report."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise AnalysisNotFoundError(analysis_id)

    # Cascade delete: patents → report → analysis
    db.query(PatentResult).filter(PatentResult.analysis_id == analysis_id).delete()
    db.query(Report).filter(Report.analysis_id == analysis_id).delete()
    db.delete(analysis)
    db.commit()

    logger.info(f"Deleted analysis {analysis_id} and all associated records.")
    return JSONResponse(content={"deleted": analysis_id})


@router.get("/dashboard", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard(db: Session = Depends(get_db)):
    """Analytics dashboard — aggregate stats over all analyses."""
    total = db.query(func.count(Analysis.id)).scalar()

    # Risk distribution
    risk_dist = {"Low Patent Risk": 0, "Requires Expert Review": 0, "High Patent Risk": 0, "Pending": 0}
    reports = db.query(Report).all()
    for r in reports:
        if r.recommendation in risk_dist:
            risk_dist[r.recommendation] += 1

    # Count analyses without report as Pending
    analyzed_ids = {r.analysis_id for r in reports}
    all_analyses = db.query(Analysis).all()
    for a in all_analyses:
        if a.id not in analyzed_ids:
            risk_dist["Pending"] += 1

    # Top indications
    indications = db.query(Analysis.indication, func.count(Analysis.id).label("count"))\
        .filter(Analysis.indication.isnot(None))\
        .group_by(Analysis.indication)\
        .order_by(desc("count"))\
        .limit(5).all()
    top_indications = [{"indication": i[0], "count": i[1]} for i in indications]

    # Top targets
    targets = db.query(Analysis.target, func.count(Analysis.id).label("count"))\
        .filter(Analysis.target.isnot(None))\
        .group_by(Analysis.target)\
        .order_by(desc("count"))\
        .limit(5).all()
    top_targets = [{"target": t[0], "count": t[1]} for t in targets]

    # Source distribution
    sources = db.query(PatentResult.source, func.count(PatentResult.id).label("count"))\
        .filter(PatentResult.source.isnot(None))\
        .group_by(PatentResult.source)\
        .all()
    source_dist = {s[0]: s[1] for s in sources}

    # Recent analyses
    recent = db.query(Analysis).order_by(desc(Analysis.created_at)).limit(5).all()
    recent_items = []
    for a in recent:
        patent_count = db.query(func.count(PatentResult.id)).filter(PatentResult.analysis_id == a.id).scalar()
        report = db.query(Report).filter(Report.analysis_id == a.id).first()
        recent_items.append(AnalysisSummary(
            id=a.id,
            smiles=a.smiles,
            molecule_name=a.molecule_name,
            target=a.target,
            indication=a.indication,
            status=a.status,
            patent_count=patent_count or 0,
            risk_level=report.recommendation if report else None,
            risk_score=report.risk_score if report else None,
            created_at=a.created_at,
        ))

    return DashboardStats(
        total_analyses=total or 0,
        risk_distribution=risk_dist,
        top_indications=top_indications,
        top_targets=top_targets,
        source_distribution=source_dist,
        recent_analyses=recent_items,
    )
