from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_question_without_upload_returns_404():
    response = client.post(
        "/api/v1/ask_question",
        json={"user_id": "fresh-user-never-uploaded", "question": "What are my strengths?"},
    )
    assert response.status_code == 404
    assert "upload your resume" in response.json()["detail"].lower()


def test_upload_rejects_bad_extension():
    response = client.post(
        "/api/v1/upload_resume",
        data={"user_id": "user-1"},
        files={"file": ("resume.exe", b"not a real resume", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_ask_question_validates_empty_question():
    response = client.post(
        "/api/v1/ask_question",
        json={"user_id": "user-1", "question": ""},
    )
    assert response.status_code == 422  # pydantic min_length validation

