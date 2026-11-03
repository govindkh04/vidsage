import pytest
from ytrag.chunk import chunk_segments, is_repetitive_hallucination
from ytrag.models import Chunk, Segment, Video


def test_repetitive_hallucination_detection():
    # Regular explanation text
    normal_text = "In this lecture we discuss dynamic programming and the difference between memoization and tabulation."
    assert not is_repetitive_hallucination(normal_text)

    # Hallucination loop repeating a 3-word phrase
    hallucination_text = "thank you for watching thank you for watching thank you for watching thank you for watching"
    assert is_repetitive_hallucination(hallucination_text)


def test_chunk_segments_boundaries_and_timestamps():
    video = Video(video_id="test_vid_123", title="Test DSA Lecture", duration=300)
    segments = [
        Segment(start=0.0, end=30.0, text="Introduction to binary search."),
        Segment(start=30.0, end=70.0, text="Dividing search space in half each iteration."),
        Segment(start=70.0, end=110.0, text="Calculating mid index without integer overflow."),
        Segment(start=110.0, end=150.0, text="Handling base conditions and returning index."),
    ]

    # Target chunk duration: 75 seconds, Overlap: 15 seconds
    chunks = chunk_segments(video, segments, chunk_seconds=75, chunk_overlap=15)

    assert len(chunks) > 0
    first_chunk = chunks[0]

    # Verify chunk structure
    assert first_chunk.video_id == "test_vid_123"
    assert first_chunk.start_sec == 0
    assert first_chunk.end_sec >= 70
    assert "Test DSA Lecture" in first_chunk.text
    assert "binary search" in first_chunk.text

    # Verify stable deterministic ID
    assert first_chunk.chunk_id == "test_vid_123:0"
    assert first_chunk.source_url == "https://www.youtube.com/watch?v=test_vid_123&t=0s"


def test_chunk_empty_segments():
    video = Video(video_id="empty_vid", title="Empty Lecture", duration=0)
    chunks = chunk_segments(video, [])
    assert chunks == []


def test_deterministic_chunk_ids_on_reprocessing():
    video = Video(video_id="vid_repeat", title="Repeat Lecture", duration=200)
    segments = [
        Segment(start=10.0, end=60.0, text="First explanation segment."),
        Segment(start=60.0, end=120.0, text="Second explanation segment."),
    ]

    run1 = chunk_segments(video, segments, chunk_seconds=75, chunk_overlap=15)
    run2 = chunk_segments(video, segments, chunk_seconds=75, chunk_overlap=15)

    assert len(run1) == len(run2)
    for c1, c2 in zip(run1, run2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.start_sec == c2.start_sec
        assert c1.end_sec == c2.end_sec
