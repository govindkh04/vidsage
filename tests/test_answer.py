import pytest
from unittest.mock import MagicMock
from ytrag.answer import (
    answer,
    build_context_block,
    extract_citation_indices,
)


def test_extract_citation_indices():
    text = "In lecture [1], we cover memoization. Later in [2], tabulation is explained. Also refer [1]."
    indices = extract_citation_indices(text)
    assert indices == [1, 2]


def test_build_context_block():
    chunks = [
        {
            "video_title": "DP Lecture 1",
            "start_sec": 120,
            "end_sec": 180,
            "text": "DP Lecture 1\n\nMemoization stores computed state.",
        },
        {
            "video_title": "DP Lecture 2",
            "start_sec": 300,
            "end_sec": 360,
            "text": "DP Lecture 2\n\nTabulation is bottom-up approach.",
        },
    ]
    context = build_context_block(chunks)
    assert "[1] Lecture: DP Lecture 1" in context
    assert "02:00 - 03:00" in context
    assert "[2] Lecture: DP Lecture 2" in context
    assert "05:00 - 06:00" in context


def test_answer_refusal_when_below_threshold(monkeypatch):
    # Mock qdrant_search to return chunk with low score
    mock_search = MagicMock(
        return_value=[
            {
                "score": 0.25,
                "video_id": "vid_xyz",
                "video_title": "Unrelated Title",
                "start_sec": 0,
                "end_sec": 50,
                "text": "Completely irrelevant content",
            }
        ]
    )
    monkeypatch.setattr("ytrag.answer.qdrant_search", mock_search)

    # Threshold set higher than 0.25
    result = answer("What is quicksort?", top_k=5, max_distance=0.40)
    assert result["grounded"] is False
    assert result["citations"] == []
    assert "cover nahi hua" in result["answer"]
