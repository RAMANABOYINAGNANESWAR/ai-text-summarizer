from fastapi.testclient import TestClient

from app.main import app
import app.main as main_module

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summarize_success(monkeypatch):
    # Mock out the LLM call so tests run offline, fast, and free
    monkeypatch.setattr(
        main_module,
        "summarize_text",
        lambda text, max_words: "This is a mocked summary.",
    )

    response = client.post("/summarize", json={"text": "Some long text " * 20})
    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == "This is a mocked summary."
    assert body["original_length_words"] == 60
    assert body["summary_length_words"] == 5


def test_summarize_rejects_empty_text():
    response = client.post("/summarize", json={"text": ""})
    assert response.status_code == 422  # Pydantic validation error


def test_summarize_upstream_failure(monkeypatch):
    def broken(text, max_words):
        raise RuntimeError("provider is down")

    monkeypatch.setattr(main_module, "summarize_text", broken)

    response = client.post("/summarize", json={"text": "hello world"})
    assert response.status_code == 502
    assert response.json()["detail"] == "provider is down"
