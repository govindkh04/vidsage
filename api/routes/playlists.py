import logging
from fastapi import APIRouter
from ytrag.config import settings
from ytrag.index import stats as qdrant_stats

logger = logging.getLogger("api.playlists")
router = APIRouter(tags=["Playlists"])


@router.get("/playlists")
def list_indexed_playlists() -> list[dict]:
    """List indexed lecture playlists."""
    try:
        s = qdrant_stats()
        return [
            {
                "collection": settings.collection_name,
                "title": "DSA Patterns 2026 (Beginner to Advanced)",
                "total_chunks": s.get("points_count", 0),
                "embed_model": s.get("embed_model", settings.embed_model),
            }
        ]
    except Exception as e:
        logger.exception("Error listing playlists")
        return []
