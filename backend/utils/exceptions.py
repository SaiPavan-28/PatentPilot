"""
Centralized exception handling for PatentPilot.
All external API failures, validation errors, and LLM timeouts flow through here.
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import httpx
import logging

logger = logging.getLogger("patentpilot.exceptions")


class PatentPilotError(Exception):
    """Base exception for PatentPilot."""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class SMILESValidationError(PatentPilotError):
    def __init__(self, smiles: str, reason: str):
        super().__init__(
            message=f"Invalid SMILES string: {reason}",
            status_code=422,
            details={"smiles": smiles, "reason": reason}
        )


class ExternalAPIError(PatentPilotError):
    def __init__(self, service: str, message: str, status_code: int = 503):
        super().__init__(
            message=f"{service} API error: {message}",
            status_code=status_code,
            details={"service": service}
        )


class LLMError(PatentPilotError):
    def __init__(self, message: str):
        super().__init__(
            message=f"LLM generation error: {message}",
            status_code=502,
            details={"provider": "groq"}
        )


class AnalysisNotFoundError(PatentPilotError):
    def __init__(self, analysis_id: str):
        super().__init__(
            message=f"Analysis {analysis_id} not found",
            status_code=404,
            details={"analysis_id": analysis_id}
        )


# ── FastAPI Exception Handlers ─────────────────────────────────────────────────

async def patentpilot_exception_handler(request: Request, exc: PatentPilotError):
    logger.error(f"PatentPilotError: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "status_code": exc.status_code
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "status_code": 422
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    with open("error.txt", "w") as f:
        f.write(traceback.format_exc())
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )
