from fastapi.testclient import TestClient

from backend.main import app


def test_healthcheck_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_suggest_returns_project_ideas():
    with TestClient(app) as client:
        response = client.post("/api/suggest", json={"prompt": "kubernetes"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_authenticated"] is False
    assert len(payload["suggestions"]) == 3
    assert {idea["difficulty_level"] for idea in payload["suggestions"]} == {
        "beginner",
        "intermediate",
        "advanced",
    }
