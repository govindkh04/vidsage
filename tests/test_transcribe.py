import json
from pathlib import Path
from ytrag.models import Segment, Video
from ytrag.transcribe import load_cached_transcript, save_transcript_atomic


def test_atomic_transcript_save_and_load(tmp_path: Path, monkeypatch):
    # Route get_transcript_cache_path to a clean temp directory
    monkeypatch.setattr(
        "ytrag.transcribe.get_transcript_cache_path",
        lambda video_id: tmp_path / f"{video_id}.json",
    )

    video = Video(video_id="atom_123", title="Atomic Test Video", duration=100)
    segments = [
        Segment(start=1.5, end=10.2, text="Atomic writing test line 1"),
        Segment(start=10.2, end=20.0, text="Atomic writing test line 2"),
    ]

    saved_path = save_transcript_atomic(
        video=video,
        segments=segments,
        language="en",
        model_name="small",
    )

    assert saved_path.is_file()
    assert not saved_path.with_suffix(".tmp").exists()

    # Load from cache
    loaded = load_cached_transcript(video.video_id)
    assert loaded is not None
    assert len(loaded) == 2
    assert loaded[0].start == 1.5
    assert loaded[0].end == 10.2
    assert loaded[0].text == "Atomic writing test line 1"
