"""
Minimal API tests — run with: pytest
These tests run against the mock mode (no real API key required).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

# Force mock mode for all tests
import app.config as _cfg
_cfg.settings.anthropic_api_key = ""


from app.main import app  # noqa: E402 (import after patching)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "text_summary" in body["capabilities"]
    assert "sentiment_analysis" in body["capabilities"]


# ---------------------------------------------------------------------------
# text_summary
# ---------------------------------------------------------------------------


def test_text_summary_success():
    resp = client.post(
        "/v1/capabilities/run",
        json={
            "capability": "text_summary",
            "input": {"text": "This is a long piece of text that needs summarizing.", "max_length": 120},
            "request_id": "test-001",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "result" in body["data"]
    assert isinstance(body["data"]["result"], str)
    assert body["meta"]["request_id"] == "test-001"
    assert body["meta"]["capability"] == "text_summary"
    assert isinstance(body["meta"]["elapsed_ms"], int)


def test_text_summary_auto_request_id():
    resp = client.post(
        "/v1/capabilities/run",
        json={"capability": "text_summary", "input": {"text": "Hello world"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["meta"]["request_id"]  # auto-generated, non-empty


def test_text_summary_missing_text():
    resp = client.post(
        "/v1/capabilities/run",
        json={"capability": "text_summary", "input": {"max_length": 50}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_INPUT"


def test_text_summary_empty_text():
    resp = client.post(
        "/v1/capabilities/run",
        json={"capability": "text_summary", "input": {"text": ""}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_INPUT"


# ---------------------------------------------------------------------------
# sentiment_analysis
# ---------------------------------------------------------------------------


def test_sentiment_analysis_success():
    resp = client.post(
        "/v1/capabilities/run",
        json={
            "capability": "sentiment_analysis",
            "input": {"text": "I absolutely love this product!"},
            "request_id": "test-sa-001",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    result = body["data"]["result"]
    assert "sentiment" in result
    assert result["sentiment"] in ("positive", "negative", "neutral")
    assert "score" in result


def test_sentiment_analysis_missing_text():
    resp = client.post(
        "/v1/capabilities/run",
        json={"capability": "sentiment_analysis", "input": {}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_INPUT"


# ---------------------------------------------------------------------------
# Unknown capability
# ---------------------------------------------------------------------------


def test_unknown_capability():
    resp = client.post(
        "/v1/capabilities/run",
        json={"capability": "does_not_exist", "input": {}},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "UNKNOWN_CAPABILITY"


# ---------------------------------------------------------------------------
# Response schema validation
# ---------------------------------------------------------------------------


def test_error_response_has_meta():
    resp = client.post(
        "/v1/capabilities/run",
        json={"capability": "unknown", "input": {}, "request_id": "meta-test"},
    )
    body = resp.json()
    assert body["meta"]["request_id"] == "meta-test"
    assert body["meta"]["capability"] == "unknown"
    assert isinstance(body["meta"]["elapsed_ms"], int)
