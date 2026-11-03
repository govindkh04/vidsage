from typing import Any, Optional

from ytrag.models import Chunk
from ytrag.services.qdrant_service import QdrantService

_service_instance: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    global _service_instance
    if _service_instance is None:
        _service_instance = QdrantService()
    return _service_instance


def upsert_chunks(chunks: list[Chunk]) -> int:
    """Upsert chunks into the configured Qdrant collection."""
    service = get_qdrant_service()
    return service.upsert_chunks(chunks)


def search(
    query: str,
    top_k: int = 6,
    video_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Search for relevant lecture chunks in Qdrant."""
    service = get_qdrant_service()
    return service.search(query=query, top_k=top_k, video_id=video_id)


def stats() -> dict[str, Any]:
    """Retrieve indexing statistics."""
    service = get_qdrant_service()
    return service.stats()
