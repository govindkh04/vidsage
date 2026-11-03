from typing import Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health and status response."""
    status: str = "ok"
    version: str = "0.1.0"
    qdrant_connected: bool
    groq_connected: bool
    collection: str
    total_indexed_chunks: int


class CitationItem(BaseModel):
    """Detailed metadata for a cited lecture segment."""
    citation_id: str = Field(..., description="Citation marker (e.g. [1])")
    video_id: str
    title: str
    start_sec: int
    end_sec: int
    timestamp: str = Field(..., description="Formatted timestamp (e.g. 02:07)")
    url: str = Field(..., description="Direct YouTube link with rewind timestamp offset")
    text: str


class AskResponse(BaseModel):
    """Grounded question answering response."""
    question: str
    answer: str
    grounded: bool
    citations: list[CitationItem]
    retrieved_count: int


class SearchResultItem(BaseModel):
    """Single semantic search result item."""
    score: float
    chunk_id: str
    video_id: str
    video_title: str
    start_sec: int
    end_sec: int
    timestamp: str
    source_url: str
    text: str


class SearchResponse(BaseModel):
    """Semantic vector search response."""
    query: str
    count: int
    results: list[SearchResultItem]


class VideoItem(BaseModel):
    """Indexed video summary item."""
    video_id: str
    title: str
    chunks_count: int
    source_url: str


class VideoDetailResponse(BaseModel):
    """Detailed information and chunks for an indexed video."""
    video_id: str
    title: str
    chunks_count: int
    source_url: str
    chunks: list[dict[str, Any]]
