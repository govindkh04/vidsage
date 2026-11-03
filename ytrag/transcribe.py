import json
import logging
import os
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel

from ytrag.config import settings
from ytrag.models import Segment, Video

logger = logging.getLogger("ytrag.transcribe")

# Cache model instance in memory so multiple calls do not reload the weights
_cached_whisper_model: Optional[WhisperModel] = None
_cached_model_key: Optional[str] = None


def get_whisper_model(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    compute_type: Optional[str] = None,
) -> WhisperModel:
    """Get or load a cached WhisperModel instance with CPU fallback support."""
    global _cached_whisper_model, _cached_model_key

    selected_model = model_name or settings.whisper_model
    selected_device = device or settings.resolved_device
    selected_compute = compute_type or settings.resolved_compute_type

    model_key = f"{selected_model}:{selected_device}:{selected_compute}"
    if _cached_whisper_model is not None and _cached_model_key == model_key:
        return _cached_whisper_model

    logger.info(
        f"Loading faster-whisper model '{selected_model}' on {selected_device.upper()} "
        f"with compute_type='{selected_compute}'..."
    )

    try:
        model = WhisperModel(
            selected_model,
            device=selected_device,
            compute_type=selected_compute,
        )
    except Exception as e:
        if selected_device == "cuda":
            logger.warning(
                f"CUDA loading failed ({e}). Falling back to CPU with compute_type='int8'..."
            )
            model = WhisperModel(
                selected_model,
                device="cpu",
                compute_type="int8",
            )
            model_key = f"{selected_model}:cpu:int8"
        else:
            raise e

    _cached_whisper_model = model
    _cached_model_key = model_key
    return model


def get_transcript_cache_path(video_id: str) -> Path:
    """Get the cached transcript path for a video."""
    return settings.transcripts_dir / f"{video_id}.json"


def load_cached_transcript(video_id: str) -> Optional[list[Segment]]:
    """Load transcript segments from cache if file exists and is valid."""
    path = get_transcript_cache_path(video_id)
    if not path.is_file():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = [
            Segment(
                start=float(s["start"]),
                end=float(s["end"]),
                text=s["text"].strip(),
            )
            for s in data.get("segments", [])
            if s.get("text", "").strip()
        ]
        logger.info(f"Loaded cached transcript for video {video_id} ({len(segments)} segments)")
        return segments
    except Exception as err:
        logger.warning(f"Failed to read cached transcript for {video_id}: {err}. Will re-transcribe.")
        return None


def save_transcript_atomic(
    video: Video,
    segments: list[Segment],
    language: str,
    model_name: str,
) -> Path:
    """Safely and atomically serialize transcript JSON using a temporary file and os.replace."""
    target_path = get_transcript_cache_path(video.video_id)
    temp_path = target_path.with_suffix(f".tmp.{os.getpid()}")

    payload = {
        "video_id": video.video_id,
        "title": video.title,
        "language": language,
        "model": model_name,
        "segments": [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
            }
            for seg in segments
        ],
    }

    # Write completely to temp file
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Atomic rename prevents partial/corrupted files if interrupted
    os.replace(temp_path, target_path)
    logger.info(f"Saved transcript atomically to {target_path}")
    return target_path


def transcribe(
    video: Video,
    audio_path: Path,
    force: bool = False,
    language: Optional[str] = None,
    model_name: Optional[str] = None,
) -> list[Segment]:
    """Transcribe audio file into timestamped Segment objects.
    
    Checks cached transcript first. Never re-transcribes if cache exists unless force is True.
    """
    # 1. Check cache
    if not force:
        cached = load_cached_transcript(video.video_id)
        if cached is not None:
            return cached

    # 2. Verify audio file exists
    if not audio_path.is_file() or audio_path.stat().st_size == 0:
        raise FileNotFoundError(f"Audio file not found or empty: {audio_path}")

    # 3. Load faster-whisper model
    active_model_name = model_name or settings.whisper_model
    model = get_whisper_model(model_name=active_model_name)

    # 4. Transcribe audio stream
    lang = language or (settings.whisper_lang if settings.whisper_lang != "auto" else None)
    logger.info(f"Transcribing '{video.title}' [audio={audio_path.name}, lang={lang or 'auto'}]...")

    raw_segments, info = model.transcribe(
        str(audio_path),
        beam_size=settings.whisper_beam,
        language=lang,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    detected_lang = info.language or "unknown"
    logger.info(f"Whisper detected language: {detected_lang} (probability={info.language_probability:.2f})")

    segments: list[Segment] = []
    for s in raw_segments:
        text = s.text.strip()
        if text:
            # Preserve raw float timestamps as returned by Whisper
            segments.append(
                Segment(
                    start=float(s.start),
                    end=float(s.end),
                    text=text,
                )
            )

    if not segments:
        logger.warning(f"Whisper produced 0 segments for video {video.video_id}")

    # 5. Save atomically to cache
    save_transcript_atomic(
        video=video,
        segments=segments,
        language=detected_lang,
        model_name=active_model_name,
    )

    return segments
