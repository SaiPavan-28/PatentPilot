"""
PatentPilot Configuration
Reads all settings from environment variables / .env file.
Fails fast on startup if required vars are missing.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "PatentPilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    DATABASE_URL: str = "sqlite:///./patentpilot.db"

    # Groq LLM
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int = 2048
    GROQ_TEMPERATURE: float = 0.3

    # External APIs
    PUBCHEM_BASE_URL: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    PATENTSVIEW_BASE_URL: str = "https://search.patentsview.org/api/v1"
    SURECHEMBL_BASE_URL: str = "https://www.surechembl.org/api"

    # Retrieval
    MAX_PATENTS_RETURNED: int = 10
    TANIMOTO_THRESHOLD: float = 0.4
    REQUEST_TIMEOUT_SECONDS: int = 30

    # Scoring Weights (must sum to 1.0)
    WEIGHT_CHEMICAL: float = 0.35
    WEIGHT_TARGET: float = 0.25
    WEIGHT_DISEASE: float = 0.20
    WEIGHT_SEMANTIC: float = 0.20

    # Risk Thresholds
    HIGH_RISK_THRESHOLD: float = 0.75
    REVIEW_THRESHOLD: float = 0.40

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
