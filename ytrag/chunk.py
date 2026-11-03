import logging
import re
from typing import Optional

from ytrag.config import settings
from ytrag.models import Chunk, Segment, Video

logger = logging.getLogger("ytrag.chunk")


def is_repetitive_hallucination(text: str, max_repeat_ratio: float = 0.5) -> bool:
    """Detect common Whisper hallucination loops (repeated short phrases)."""
    words = text.lower().split()
    if len(words) < 6:
        return False

    # Check 3-word n-gram repetitions
    trigrams = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]
    if not trigrams:
        return False

    from collections import Counter
    counts = Counter(trigrams)
    most_common_count = counts.most_common(1)[0][1]

    # If the same 3-word phrase makes up more than 50% of the text, it is a hallucination
    if most_common_count * 3 / len(words) > max_repeat_ratio:
        return True

    return False


def chunk_segments(
    video: Video,
    segments: list[Segment],
    chunk_seconds: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[Chunk]:
    """Divide Whisper segments into time-based retrieval chunks preserving exact timestamps.
    
    Rules:
    - Never split a Whisper segment.
    - Accumulate complete segments until target window (default 75s) is reached.
    - Emit Chunk with stable deterministic ID: '{video_id}:{start_sec}'.
    - Prefix chunk text with lecture title to improve dense vector retrieval.
    - Backtrack using overlap (default 15s) to the appropriate segment boundary.
    - Filter noise and repetitive hallucinations.
    """
    if not segments:
        return []

    target_duration = chunk_seconds if chunk_seconds is not None else settings.chunk_seconds
    overlap_duration = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap

    # Guard against invalid overlap configurations
    if overlap_duration >= target_duration:
        overlap_duration = max(0, target_duration - 15)

    chunks: list[Chunk] = []
    n = len(segments)
    current_idx = 0
    seen_chunk_ids: set[str] = set()

    while current_idx < n:
        chunk_start_sec = int(segments[current_idx].start)
        window_end_time = segments[current_idx].start + target_duration

        accumulated_texts: list[str] = []
        end_idx = current_idx

        # Accumulate segments until window_end_time is reached or end of transcript
        while end_idx < n:
            seg = segments[end_idx]
            accumulated_texts.append(seg.text)
            end_idx += 1
            if seg.end >= window_end_time:
                break

        chunk_end_sec = int(segments[end_idx - 1].end)
        combined_text = " ".join(accumulated_texts).strip()

        # Noise & hallucination filters
        if combined_text and not is_repetitive_hallucination(combined_text):
            # Prefix chunk text with lecture title for enhanced context
            prefixed_text = f"{video.title}\n\n{combined_text}"
            chunk_id = f"{video.video_id}:{chunk_start_sec}"

            if chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        video_id=video.video_id,
                        video_title=video.title,
                        start_sec=chunk_start_sec,
                        end_sec=max(chunk_end_sec, chunk_start_sec + 1),
                        text=prefixed_text,
                    )
                )

        # Reached the end of transcript
        if end_idx >= n:
            break

        # Calculate overlap backtrack point
        overlap_boundary_time = segments[end_idx - 1].end - overlap_duration
        next_idx = end_idx

        # Backtrack to find first segment starting after or at overlap_boundary_time
        for i in range(current_idx + 1, end_idx):
            if segments[i].start >= overlap_boundary_time:
                next_idx = i
                break

        # Prevent infinite loops: index must always advance
        if next_idx <= current_idx:
            next_idx = current_idx + 1

        current_idx = next_idx

    logger.info(f"Generated {len(chunks)} timestamped chunks for '{video.title}'")
    return chunks
