from typing import Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request payload for answering a question via grounded RAG."""
    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="User question in English or Hinglish.",
        examples=["Video schedule ke baare me kya bataya gaya hai?"],
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of chunks to retrieve from Qdrant.",
    )
    threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance similarity threshold (0.0 to 1.0).",
    )


class SearchRequest(BaseModel):
    """Request payload for semantic lecture search without LLM generation."""
    query: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Search keywords or concept description.",
        examples=["two pointer pattern roadmap"],
    )
    top_k: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Maximum number of retrieved segments.",
    )
    video_id: Optional[str] = Field(
        default=None,
        description="Optional video ID filter to restrict search to one lecture.",
    )
