import logging
from collections import defaultdict
from typing import Any
from fastapi import APIRouter, HTTPException, status
from qdrant_client.http import models as qmodels

from api.schemas.response import VideoDetailResponse, VideoItem
from ytrag.config import settings
from ytrag.index import get_qdrant_service

logger = logging.getLogger("api.videos")
router = APIRouter(tags=["Videos"])


@router.get("/videos", response_model=list[VideoItem])
def list_indexed_videos() -> list[VideoItem]:
    """List all videos currently indexed in the vector database."""
    try:
        service = get_qdrant_service()
        records, _ = service.client.scroll(
            collection_name=settings.collection_name,
            limit=5000,
            with_payload=True,
            with_vectors=False,
        )

        video_map: dict[str, dict[str, Any]] = {}
        for r in records:
            payload = r.payload or {}
            vid_id = payload.get("video_id")
            if not vid_id:
                continue
            if vid_id not in video_map:
                video_map[vid_id] = {
                    "video_id": vid_id,
                    "title": payload.get("video_title", "Unknown Lecture"),
                    "chunks_count": 0,
                    "source_url": f"https://www.youtube.com/watch?v={vid_id}",
                }
            video_map[vid_id]["chunks_count"] += 1

        return [VideoItem(**v) for v in video_map.values()]

    except Exception as e:
        logger.exception("Error listing indexed videos")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve indexed videos: {str(e)}",
        )


@router.get("/videos/{video_id}", response_model=VideoDetailResponse)
def get_video_details(video_id: str) -> VideoDetailResponse:
    """Retrieve detailed chunks and metadata for a specific indexed video."""
    try:
        service = get_qdrant_service()
        records, _ = service.client.scroll(
            collection_name=settings.collection_name,
            scroll_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="video_id",
                        match=qmodels.MatchValue(value=video_id),
                    )
                ]
            ),
            limit=500,
            with_payload=True,
            with_vectors=False,
        )

        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video '{video_id}' is not indexed in the knowledge base.",
            )

        title = records[0].payload.get("video_title", "Unknown Lecture") if records[0].payload else "Unknown Lecture"
        chunks = [r.payload for r in records if r.payload]
        chunks.sort(key=lambda x: x.get("start_sec", 0))

        return VideoDetailResponse(
            video_id=video_id,
            title=title,
            chunks_count=len(chunks),
            source_url=f"https://www.youtube.com/watch?v={video_id}",
            chunks=chunks,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching details for video {video_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching video details: {str(e)}",
        )
