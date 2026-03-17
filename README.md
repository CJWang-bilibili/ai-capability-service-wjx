# AI Capability Service

A production-ready backend service that provides a unified API for invoking AI model capabilities.

## Features

- `POST /v1/capabilities/run` — unified capability dispatch endpoint
- `text_summary` — summarize long text (with optional `max_length`)
- `sentiment_analysis` — classify text sentiment with a confidence score
- Real Claude API integration (claude-opus-4-6) with graceful mock fallback
- Structured logging with `request_id` propagation and elapsed-time tracking
- `/healthz` endpoint for liveness checks
- 9 automated tests (no API key required)

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

> **No key?** Leave `ANTHROPIC_API_KEY` blank — the service starts in **mock mode** and returns
> pre-canned responses. All endpoints still work, so you can explore the API without a key.

### 3. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now available at `http://localhost:8000`.

---

## Example Requests

### text_summary

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "text_summary",
    "input": {
      "text": "Artificial intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.",
      "max_length": 120
    },
    "request_id": "my-req-001"
  }'
```

Success response:

```json
{
  "ok": true,
  "data": {
    "result": "AI simulates human intelligence in machines, enabling them to learn and solve problems."
  },
  "meta": {
    "request_id": "my-req-001",
    "capability": "text_summary",
    "elapsed_ms": 843
  }
}
```

### sentiment_analysis

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "sentiment_analysis",
    "input": {
      "text": "I absolutely love this product! Best purchase I have made all year."
    }
  }'
```

Success response:

```json
{
  "ok": true,
  "data": {
    "result": {
      "sentiment": "positive",
      "score": 0.97,
      "explanation": "The text expresses strong enthusiasm and satisfaction."
    }
  },
  "meta": {
    "request_id": "f3a1c2d4-...",
    "capability": "sentiment_analysis",
    "elapsed_ms": 612
  }
}
```

### Error response (example)

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{"capability": "text_summary", "input": {}}'
```

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "'text' field is required and must be a non-empty string",
    "details": {}
  },
  "meta": {
    "request_id": "...",
    "capability": "text_summary",
    "elapsed_ms": 1
  }
}
```

### Health check

```bash
curl http://localhost:8000/healthz
```

---

## Running Tests

Tests run in mock mode — no API key required.

```bash
pytest
```

---

## Project Structure

```
app/
  main.py                  # FastAPI app, routing, logging
  config.py                # Settings (reads .env)
  models.py                # Pydantic request/response schemas
  capabilities/
    base.py                # Abstract base + CapabilityError
    registry.py            # Capability registry
    text_summary.py        # text_summary capability
    sentiment_analysis.py  # sentiment_analysis capability
tests/
  test_api.py              # API tests (mock mode)
.env.example               # Environment variable template
requirements.txt
```

---

## How to Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to **API Keys** in the left sidebar
4. Click **Create Key**
5. Copy the key (it starts with `sk-ant-`) and paste it into your `.env` file

> The service uses **claude-opus-4-6** by default. Costs are billed per token — see
> [Anthropic pricing](https://www.anthropic.com/pricing) for details.

---

## API Reference

### `POST /v1/capabilities/run`

| Field | Type | Required | Description |
|---|---|---|---|
| `capability` | string | yes | Capability to invoke (`text_summary`, `sentiment_analysis`) |
| `input` | object | yes | Capability-specific input (see below) |
| `request_id` | string | no | Idempotency / tracing ID (auto-generated if omitted) |

#### `text_summary` input

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | yes | Text to summarize |
| `max_length` | integer | no | Max characters in the summary (default: 150) |

#### `sentiment_analysis` input

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | yes | Text to analyze |
