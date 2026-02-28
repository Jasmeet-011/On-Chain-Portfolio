from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/health")
def health():
    """Basic health check."""
    return {"ok": True}


@router.get("/health/detailed")
def health_detailed() -> Dict[str, Any]:
    """
    Detailed health check with cache and system status.

    Returns:
        System health information including cache status
    """
    from app.services.cache import cache

    return {
        "ok": True,
        "cache": cache.get_stats(),
        "version": "0.4.0",
    }
