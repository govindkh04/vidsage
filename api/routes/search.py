import logging
from fastapi import APIRouter, HTTPException, status
from api.schemas.request import SearchRequest
from api.schemas.response import SearchResponse, SearchResultItem
from ytrag.index import search as qdrant_search
from ytrag.models import format_timestamp

logger = logging.getLogger("api.search")
router = APIRouter(tags=["Search"])


@router.post("/search", response_model=SearchResponse)
def search_chunks(req: SearchRequest) -> SearchResponse:
    """Retrieve raw relevant lecture chunks from Qdrant without invoking the LLM."""
    try:
        raw_results = qdrant_search(
            query=req.query,
            top_k=req.top_k,
            video_id=req.video_id,
        )
    except Exception as e:
        logger.exception("Error executing vector search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while querying vector index: {str(e)}",
        )

    items: list[SearchResultItem] = []
    for r in raw_results:
        items.append(
            SearchResultItem(
                score=r.get("score", 0.0),
                chunk_id=r.get("chunk_id", ""),
                video_id=r.get("video_id", ""),
                video_title=r.get("video_title", ""),
                start_sec=r.get("start_sec", 0),
                end_sec=r.get("end_sec", 0),
                timestamp=f"{format_timestamp(r.get('start_sec', 0))} - {format_timestamp(r.get('end_sec', 0))}",
                source_url=r.get("source_url", ""),
                text=r.get("text", ""),
            )
        )

    return SearchResponse(
        query=req.query,
        count=len(items),
        results=items,
    )
