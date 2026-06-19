from fastapi import APIRouter

from src.core.config import get_settings


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, object]:
    settings = get_settings()

    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": settings.app_name,
        },
    }
