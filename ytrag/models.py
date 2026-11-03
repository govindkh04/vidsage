from dataclasses import dataclass
from typing import Optional


def format_timestamp(seconds: float | int) -> str:
    """Format seconds into HH:MM:SS or MM:SS string."""
    total_seconds = max(0, int(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


@dataclass
class Video:
    """Represents a YouTube video metadata."""
    video_id: str
    title: str
    duration: int
    playlist_id: Optional[str] = None

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


@dataclass
class Segment:
    """Raw transcription segment from Whisper with precise float timestamps."""
    start: float
    end: float
    text: str


@dataclass
class Chunk:
    """Timestamp-aware retrieval unit."""
    chunk_id: str
    video_id: str
    video_title: str
    start_sec: int
    end_sec: int
    text: str

    @property
    def source_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}&t={self.start_sec}s"

    @property
    def timestamp(self) -> str:
        return format_timestamp(self.start_sec)


@dataclass
class Citation:
    """Structured citation referencing an exact moment in a lecture."""
    video_id: str
    title: str
    start_sec: int
    end_sec: int
    timestamp: str
    url: str
    text: str

    @classmethod
    def from_chunk(cls, chunk: Chunk, rewind_sec: int = 5) -> "Citation":
        effective_start = max(0, chunk.start_sec - rewind_sec)
        return cls(
            video_id=chunk.video_id,
            title=chunk.video_title,
            start_sec=chunk.start_sec,
            end_sec=chunk.end_sec,
            timestamp=format_timestamp(chunk.start_sec),
            url=f"https://www.youtube.com/watch?v={chunk.video_id}&t={effective_start}s",
            text=chunk.text,
        )
