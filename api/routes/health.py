from fastapi import APIRouter
from api.schemas.response import HealthResponse
from ytrag.config import settings
from ytrag.index import stats as qdrant_stats
from ytrag.services.groq_service import get_groq_client

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """System health check endpoint verifying vector database and LLM connections."""
    qdrant_ok = False
    groq_ok = False
    points = 0
    collection = settings.collection_name

    # Check Qdrant
    try:
        s = qdrant_stats()
        qdrant_ok = (s.get("status") in ["green", "yellow", "ok"])
        points = s.get("points_count", 0)
    except Exception:
        qdrant_ok = False

    # Check Groq
    try:
        client = get_groq_client()
        models = client.models.list()
        groq_ok = len(models.data) > 0
    except Exception:
        groq_ok = False

    overall_status = "ok" if (qdrant_ok and groq_ok) else "degraded"

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        qdrant_connected=qdrant_ok,
        groq_connected=groq_ok,
        collection=collection,
        total_indexed_chunks=points,
    )
