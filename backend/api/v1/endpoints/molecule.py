"""
Molecule submission and validation endpoints.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from backend.db.database import get_db
from backend.db.models import Analysis
from backend.models.schemas import (
    MoleculeSubmitRequest, MoleculeValidateRequest,
    MoleculeValidateResponse, AnalysisCreateResponse
)
from backend.utils.validation import validate_smiles, get_molecule_properties, generate_structure_svg
from backend.utils.exceptions import SMILESValidationError
from backend.utils.logging import log_pipeline_stage

logger = logging.getLogger("patentpilot.api.molecule")
router = APIRouter()


@router.post("/molecule/validate", response_model=MoleculeValidateResponse, tags=["Molecule"])
async def validate_molecule(request: MoleculeValidateRequest):
    """
    Validate a SMILES string and return molecular properties + 2D structure SVG.
    Client-side use: call this on blur to give instant feedback.
    """
    log_pipeline_stage(logger, "SMILES_VALIDATION", {"smiles": request.smiles[:50]})

    is_valid, canonical, error = validate_smiles(request.smiles)
    if not is_valid:
        return MoleculeValidateResponse(valid=False, smiles=request.smiles, error=error)

    props = get_molecule_properties(canonical)
    svg = generate_structure_svg(canonical)

    return MoleculeValidateResponse(
        valid=True,
        smiles=request.smiles,
        canonical_smiles=canonical,
        molecular_formula=props.get("molecular_formula"),
        molecular_weight=props.get("molecular_weight"),
        num_atoms=props.get("num_atoms"),
        structure_svg=svg,
    )


@router.post("/molecule/submit", response_model=AnalysisCreateResponse, tags=["Molecule"])
async def submit_molecule(
    request: MoleculeSubmitRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Submit a molecule for FTO analysis.
    Validates SMILES, creates an Analysis record, and kicks off the retrieval pipeline.
    """
    # Step 1: Validate SMILES
    is_valid, canonical_smiles, error = validate_smiles(request.smiles)
    if not is_valid:
        raise SMILESValidationError(smiles=request.smiles, reason=error or "Invalid SMILES")

    # Step 2: Generate structure SVG
    svg = generate_structure_svg(canonical_smiles)

    # Step 3: Create analysis record
    analysis = Analysis(
        id=str(uuid.uuid4()),
        smiles=canonical_smiles,
        molecule_name=request.molecule_name,
        target=request.target,
        indication=request.indication,
        status="processing",
        structure_svg=svg,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    log_pipeline_stage(logger, "ANALYSIS_CREATED", {
        "message": f"Analysis {analysis.id} created",
        "smiles": canonical_smiles[:50],
        "target": request.target,
        "indication": request.indication,
    })

    props = get_molecule_properties(canonical_smiles)
    inchikey = props.get("inchikey")

    # Step 4: Kick off pipeline in background
    background_tasks.add_task(run_analysis_pipeline, analysis.id, canonical_smiles, request.target, request.indication, inchikey)

    return AnalysisCreateResponse(
        id=analysis.id,
        status=analysis.status,
        smiles=analysis.smiles,
        molecule_name=analysis.molecule_name,
        target=analysis.target,
        indication=analysis.indication,
        structure_svg=svg,
        created_at=analysis.created_at,
    )


async def run_analysis_pipeline(analysis_id: str, smiles: str, target: str, indication: str, inchikey: str = None):
    """
    Background task: run the full retrieval → ranking → explanation pipeline.
    Updates the analysis record as stages complete.
    """
    from backend.db.database import SessionLocal
    from backend.db.models import PatentResult, ReviewStatus
    from backend.retrieval.agent import retrieve_patents
    from backend.ranking.agent import merge_and_deduplicate, rank_patents
    from backend.ai.explanation_agent import generate_patent_explanation
    import asyncio

    db = SessionLocal()
    try:
        logger.info(f"Starting pipeline for analysis {analysis_id}")

        # Stage 1: Retrieve patents
        raw_patents = await retrieve_patents(smiles, target, indication, inchikey)

        # Stage 2: Rank patents (merge + deduplicate is done inside retrieval agent already)
        ranked = rank_patents(raw_patents, smiles, target, indication, top_n=25)
        # Filter out 0-match patents if we have enough
        ranked = [p for p in ranked if p.get("overall_score", 0) > 0.05 or len(ranked) < 5]

        if not ranked:
            # Try with a broader search
            logger.info("No patents found, updating status to complete with empty results")
            db.query(Analysis).filter(Analysis.id == analysis_id).update({"status": "complete"})
            db.commit()
            return

        # Stage 3: Generate explanations (concurrent, up to 5 at a time)
        async def explain_patent(patent_data):
            return await generate_patent_explanation(patent_data, smiles, target, indication)

        # Batch LLM calls to avoid rate limiting
        explanations = []
        for i in range(0, len(ranked), 5):
            batch = ranked[i:i+5]
            batch_results = await asyncio.gather(*[explain_patent(p) for p in batch], return_exceptions=True)
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Explanation failed for patent {batch[j].get('patent_number')}: {result}")
                    explanations.append(None)
                else:
                    explanations.append(result)
            await asyncio.sleep(0.5)  # Brief pause between batches

        # Stage 4: Persist to DB
        for i, patent_data in enumerate(ranked):
            patent_record = PatentResult(
                analysis_id=analysis_id,
                patent_number=patent_data.get("patent_number", ""),
                title=patent_data.get("title"),
                abstract=patent_data.get("abstract"),
                claims=patent_data.get("claims"),
                assignee=patent_data.get("assignee"),
                publication_date=patent_data.get("publication_date"),
                source=patent_data.get("source"),
                patent_url=patent_data.get("patent_url"),
                pdf_url=patent_data.get("pdf_url"),
                uspto_url=patent_data.get("uspto_url"),
                epo_url=patent_data.get("epo_url"),
                google_patents_url=patent_data.get("google_patents_url"),
                verification_status=patent_data.get("verification_status", {}),
                chemical_similarity=patent_data.get("chemical_similarity", 0.0),
                target_match=patent_data.get("target_match", 0.0),
                disease_match=patent_data.get("disease_match", 0.0),
                semantic_relevance=patent_data.get("semantic_relevance", 0.0),
                overall_score=patent_data.get("overall_score", 0.0),
                confidence_score=patent_data.get("confidence_score", 0.0),
                evidence_flags=patent_data.get("evidence_flags", []),
                explanation=explanations[i] if i < len(explanations) else None,
                explanation_generated=bool(explanations[i] if i < len(explanations) else None),
                rank=patent_data.get("rank", i + 1),
            )
            db.add(patent_record)
            db.flush()

            # Create default review status
            review = ReviewStatus(
                analysis_id=analysis_id,
                patent_id=patent_record.id,
                status="unreviewed",
            )
            db.add(review)

        db.query(Analysis).filter(Analysis.id == analysis_id).update({"status": "complete"})
        db.commit()
        logger.info(f"Pipeline complete for analysis {analysis_id} — {len(ranked)} patents stored")

    except Exception as e:
        logger.error(f"Pipeline error for analysis {analysis_id}: {e}")
        db.query(Analysis).filter(Analysis.id == analysis_id).update({"status": "error"})
        db.commit()
    finally:
        db.close()
