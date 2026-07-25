"""
Pydantic schemas (DTOs) for PatentPilot API request/response models.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "Low Patent Risk"
    REVIEW = "Requires Expert Review"
    HIGH = "High Patent Risk"


class ReviewStatusEnum(str, Enum):
    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"
    FLAGGED = "flagged"
    DISMISSED = "dismissed"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


# ── Molecule ───────────────────────────────────────────────────────────────────

class MoleculeSubmitRequest(BaseModel):
    smiles: str = Field(..., description="SMILES string for the molecule", min_length=1)
    molecule_name: Optional[str] = Field(None, description="Optional common/IUPAC name")
    target: Optional[str] = Field(None, description="Biological target (e.g., EGFR kinase)")
    indication: Optional[str] = Field(None, description="Disease/therapeutic indication")

    @validator("smiles")
    def smiles_not_empty(cls, v):
        if not v.strip():
            raise ValueError("SMILES string cannot be empty")
        return v.strip()


class MoleculeValidateRequest(BaseModel):
    smiles: str


class MoleculeValidateResponse(BaseModel):
    valid: bool
    smiles: str
    canonical_smiles: Optional[str] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    num_atoms: Optional[int] = None
    inchi: Optional[str] = None
    inchikey: Optional[str] = None
    structure_svg: Optional[str] = None
    error: Optional[str] = None


# ── Score Breakdown ────────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    chemical_similarity: float = Field(0.0, ge=0, le=1)
    target_match: float = Field(0.0, ge=0, le=1)
    disease_match: float = Field(0.0, ge=0, le=1)
    semantic_relevance: float = Field(0.0, ge=0, le=1)
    overall_score: float = Field(0.0, ge=0, le=1)
    confidence_score: float = Field(0.0, ge=0, le=1)
    evidence_flags: List[str] = []


# ── Patent Explanation ─────────────────────────────────────────────────────────

class PatentExplanation(BaseModel):
    why_retrieved: str
    similar_regions: str
    possible_novelty_overlap: str
    confidence: str
    risk_level: str
    key_concerns: List[str] = []


# ── Patent ────────────────────────────────────────────────────────────────────

class PatentBase(BaseModel):
    patent_number: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    claims: Optional[str] = None
    assignee: Optional[str] = None
    publication_date: Optional[str] = None
    source: Optional[str] = None
    patent_url: Optional[str] = None
    pdf_url: Optional[str] = None
    uspto_url: Optional[str] = None
    epo_url: Optional[str] = None
    google_patents_url: Optional[str] = None
    verification_status: dict = {"surechembl": False, "patentsview": False, "pubchem": False, "google_patents": False}


class PatentResponse(PatentBase):
    id: str
    analysis_id: str
    scores: ScoreBreakdown
    explanation: Optional[PatentExplanation] = None
    explanation_generated: bool = False
    rank: int = 0
    review_status: Optional[str] = "unreviewed"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Analysis ───────────────────────────────────────────────────────────────────

class AnalysisCreateResponse(BaseModel):
    id: str
    status: str
    smiles: str
    molecule_name: Optional[str] = None
    target: Optional[str] = None
    indication: Optional[str] = None
    structure_svg: Optional[str] = None
    created_at: Optional[datetime] = None


class AnalysisSummary(BaseModel):
    id: str
    smiles: str
    molecule_name: Optional[str] = None
    target: Optional[str] = None
    indication: Optional[str] = None
    status: str
    patent_count: int = 0
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisDetailResponse(BaseModel):
    id: str
    smiles: str
    molecule_name: Optional[str] = None
    target: Optional[str] = None
    indication: Optional[str] = None
    status: str
    structure_svg: Optional[str] = None
    patents: List[PatentResponse] = []
    report: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Report ─────────────────────────────────────────────────────────────────────

class ReportGenerateRequest(BaseModel):
    analysis_id: str


class ReportResponse(BaseModel):
    id: str
    analysis_id: str
    executive_summary: Optional[str] = None
    key_similar_patents: List[Any] = []
    novelty_concerns: List[str] = []
    patents_requiring_review: List[Any] = []
    potential_novel_regions: Optional[str] = None
    recommended_next_actions: List[str] = []
    manual_review_checklist: List[str] = []
    key_evidence: List[str] = []
    recommendation: Optional[str] = None
    risk_score: Optional[float] = None
    confidence_score: Optional[float] = None
    recommendation_rationale: Optional[str] = None
    scoring_methodology_explanation: Optional[str] = None
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Review Status ─────────────────────────────────────────────────────────────

class ReviewStatusUpdate(BaseModel):
    status: ReviewStatusEnum
    notes: Optional[str] = None


class ReviewStatusResponse(BaseModel):
    patent_id: str
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ── History / Dashboard ────────────────────────────────────────────────────────

class HistoryListResponse(BaseModel):
    items: List[AnalysisSummary]
    total: int
    page: int
    per_page: int


class DashboardStats(BaseModel):
    total_analyses: int
    risk_distribution: dict
    top_indications: List[dict]
    top_targets: List[dict]
    source_distribution: dict
    recent_analyses: List[AnalysisSummary]


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool
    environment: str
