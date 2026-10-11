from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.env,
        "storage_backend": settings.storage_backend,
    }


@router.post("/seed")
def seed_demo_data(reset: bool = True):
    from scripts.seed_local import seed_local
    seed_local("data/sample", reset=reset)
    return {
        "status": "success",
        "message": "Demo datasets seeded successfully across Air, Water, and Waste tracks.",
    }
