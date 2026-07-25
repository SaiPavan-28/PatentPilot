"""
SQLAlchemy ORM Models for PatentPilot.
Tables: analyses, patents, reports, review_status
"""
from sqlalchemy import Column, String, Float, DateTime, Text, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from backend.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Analysis(Base):
    """Represents a single molecule submission and FTO analysis."""
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=generate_uuid)
    smiles = Column(Text, nullable=False)
    molecule_name = Column(String, nullable=True)
    target = Column(String, nullable=True)
    indication = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, processing, complete, error
    structure_svg = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    patents = relationship("PatentResult", back_populates="analysis", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    review_statuses = relationship("ReviewStatus", back_populates="analysis", cascade="all, delete-orphan")


class PatentResult(Base):
    """A retrieved and ranked patent associated with an analysis."""
    __tablename__ = "patents"

    id = Column(String, primary_key=True, default=generate_uuid)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)

    # Patent metadata
    patent_number = Column(String, nullable=False)
    title = Column(Text, nullable=True)
    abstract = Column(Text, nullable=True)
    claims = Column(Text, nullable=True)
    assignee = Column(String, nullable=True)
    publication_date = Column(String, nullable=True)
    source = Column(String, nullable=True)  # pubchem, patentsview, surechembl
    patent_url = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    uspto_url = Column(String, nullable=True)
    epo_url = Column(String, nullable=True)
    google_patents_url = Column(String, nullable=True)

    # Verification status
    verification_status = Column(JSON, default=lambda: {"surechembl": False, "patentsview": False, "pubchem": False, "google_patents": False})

    # Scoring (four components)
    chemical_similarity = Column(Float, default=0.0)
    target_match = Column(Float, default=0.0)
    disease_match = Column(Float, default=0.0)
    semantic_relevance = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)

    # Evidence flags
    evidence_flags = Column(JSON, default=list)

    # AI Explanation
    explanation = Column(JSON, nullable=True)  # structured explanation from LLM
    explanation_generated = Column(Boolean, default=False)

    rank = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="patents")
    review_status = relationship("ReviewStatus", back_populates="patent", uselist=False)


class Report(Base):
    """The structured patentability report for an analysis."""
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False, unique=True)

    # Report sections
    executive_summary = Column(Text, nullable=True)
    key_similar_patents = Column(JSON, default=list)
    novelty_concerns = Column(JSON, default=list)
    patents_requiring_review = Column(JSON, default=list)
    potential_novel_regions = Column(Text, nullable=True)
    recommended_next_actions = Column(JSON, default=list)
    manual_review_checklist = Column(JSON, default=list)
    key_evidence = Column(JSON, default=list)

    # Risk assessment
    recommendation = Column(String, nullable=True)  # Low Patent Risk / Requires Expert Review / High Patent Risk
    risk_score = Column(Float, nullable=True)  # 0-1 numeric
    confidence_score = Column(Float, nullable=True)  # 0-1 numeric
    recommendation_rationale = Column(Text, nullable=True)
    scoring_methodology_explanation = Column(Text, nullable=True)

    generated_at = Column(DateTime, server_default=func.now())

    # Relationship
    analysis = relationship("Analysis", back_populates="report")


class ReviewStatus(Base):
    """Per-patent review state set by the researcher."""
    __tablename__ = "review_status"

    id = Column(String, primary_key=True, default=generate_uuid)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    patent_id = Column(String, ForeignKey("patents.id"), nullable=False)
    status = Column(String, default="unreviewed")  # unreviewed, reviewed, flagged, dismissed
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="review_statuses")
    patent = relationship("PatentResult", back_populates="review_status")
