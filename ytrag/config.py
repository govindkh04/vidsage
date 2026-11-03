from pathlib import Path
from typing import Literal
import os
import torch
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for VidSage (ytrag)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Credentials
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")

    # Storage paths
    ytrag_root: str = Field(default="~/.ytrag", alias="YTRAG_ROOT")

    # Whisper Settings
    whisper_model: str = Field(default="large-v3", alias="YTRAG_WHISPER_MODEL")
    whisper_device: str = Field(default="auto", alias="YTRAG_WHISPER_DEVICE")
    whisper_compute_type: str = Field(default="auto", alias="YTRAG_WHISPER_COMPUTE_TYPE")
    whisper_batch: int = Field(default=8, alias="YTRAG_WHISPER_BATCH")
    whisper_beam: int = Field(default=5, alias="YTRAG_WHISPER_BEAM")
    whisper_lang: str = Field(default="en", alias="YTRAG_WHISPER_LANG")

    # Embeddings
    embed_model: str = Field(default="BAAI/bge-m3", alias="YTRAG_EMBED_MODEL")

    # Qdrant Vector DB
    collection_name: str = Field(default="dsa_lectures_1024", alias="YTRAG_COLLECTION")

    # Time-based Chunking (seconds)
    chunk_seconds: int = Field(default=75, alias="YTRAG_CHUNK_SECONDS")
    chunk_overlap: int = Field(default=15, alias="YTRAG_CHUNK_OVERLAP")

    # Retrieval
    top_k: int = Field(default=6, alias="YTRAG_TOP_K")
    max_distance: float = Field(default=0.40, alias="YTRAG_MAX_DISTANCE")

    # LLM Settings
    llm_model: str = Field(default="openai/gpt-oss-120b", alias="YTRAG_LLM_MODEL")

    # Rate Limiting & Safety
    rate_limit_requests: int = Field(default=30, alias="YTRAG_RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="YTRAG_RATE_LIMIT_WINDOW")
    max_question_chars: int = Field(default=1000, alias="YTRAG_MAX_QUESTION_CHARS")

    @property
    def root_dir(self) -> Path:
        """Resolved root path (~/.ytrag expanded)."""
        expanded = Path(os.path.expanduser(self.ytrag_root)).resolve()
        expanded.mkdir(parents=True, exist_ok=True)
        return expanded

    @property
    def audio_dir(self) -> Path:
        """Directory for temporary downloaded lecture audio."""
        path = self.root_dir / "audio"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def transcripts_dir(self) -> Path:
        """Directory for cached lecture transcripts."""
        path = self.root_dir / "transcripts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def langtest_dir(self) -> Path:
        """Directory for language test outputs."""
        path = self.root_dir / "langtest"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_device(self) -> str:
        """Resolve 'auto' device to 'cuda' if torch.cuda is available, else 'cpu'."""
        if self.whisper_device.lower() == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return self.whisper_device.lower()

    @property
    def resolved_compute_type(self) -> str:
        """Resolve 'auto' compute type based on resolved device."""
        if self.whisper_compute_type.lower() == "auto":
            return "float16" if self.resolved_device == "cuda" else "int8"
        return self.whisper_compute_type.lower()

    def validate_for_indexing(self) -> None:
        """Ensure Qdrant credentials are present for vector indexing/search."""
        if not self.qdrant_url:
            raise ValueError("QDRANT_URL is required but not set. Please configure it in .env.")
        if not self.qdrant_api_key:
            raise ValueError("QDRANT_API_KEY is required but not set. Please configure it in .env.")

    def validate_for_answering(self) -> None:
        """Ensure both Qdrant and Groq credentials are set for RAG question answering."""
        self.validate_for_indexing()
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for answer generation. Please configure it in .env.")


# Global singleton settings instance
settings = Settings()
