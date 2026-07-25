"""
API v1 router — aggregates all endpoint routers.
"""
from fastapi import APIRouter
from backend.api.v1.endpoints import health, molecule, patents, report, history

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(molecule.router)
router.include_router(patents.router)
router.include_router(report.router)
router.include_router(history.router)
