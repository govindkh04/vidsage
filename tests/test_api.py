import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "VidSage API"
    assert data["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "qdrant_connected" in data
    assert "groq_connected" in data


def test_ask_validation_error_on_empty_question():
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422


def test_ask_validation_error_on_too_long_question():
    long_q = "a" * 1050
    response = client.post("/ask", json={"question": long_q})
    assert response.status_code == 422


def test_ask_endpoint_success(monkeypatch):
    # Mock generate_answer to test API response serialization cleanly
    mock_answer = {
        "question": "What is two pointer pattern?",
        "answer": "Two pointer pattern uses two indices to traverse an array. [1]",
        "grounded": True,
        "citations": [
            {
                "citation_id": "[1]",
                "video_id": "test_vid",
                "title": "Two Pointer Lecture",
                "start_sec": 60,
                "end_sec": 120,
                "timestamp": "01:00",
                "url": "https://www.youtube.com/watch?v=test_vid&t=55s",
                "text": "Two pointer approach reduces quadratic time.",
            }
        ],
        "retrieved_count": 1,
    }
    monkeypatch.setattr("api.routes.ask.generate_answer", lambda **kwargs: mock_answer)

    response = client.post("/ask", json={"question": "What is two pointer pattern?"})
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert len(data["citations"]) == 1
    assert data["citations"][0]["citation_id"] == "[1]"
    assert data["citations"][0]["timestamp"] == "01:00"


def test_search_endpoint(monkeypatch):
    mock_results = [
        {
            "score": 0.58,
            "chunk_id": "vid:10",
            "video_id": "vid",
            "video_title": "DSA Lecture",
            "start_sec": 10,
            "end_sec": 70,
            "source_url": "https://youtube.com/watch?v=vid&t=10s",
            "text": "DSA Lecture\n\nSearch space definition.",
        }
    ]
    monkeypatch.setattr("api.routes.search.qdrant_search", lambda **kwargs: mock_results)

    response = client.post("/search", json={"query": "binary search space"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["score"] == 0.58


def test_list_videos_endpoint(monkeypatch):
    mock_video_record = MagicMock()
    mock_video_record.payload = {
        "video_id": "vid_abc",
        "video_title": "Array Patterns",
    }
    mock_service = MagicMock()
    mock_service.client.scroll.return_value = ([mock_video_record], None)
    monkeypatch.setattr("api.routes.videos.get_qdrant_service", lambda: mock_service)

    response = client.get("/videos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["video_id"] == "vid_abc"
    assert data[0]["chunks_count"] == 1
