# BreakMyAgent

AI agent safety sandbox for stress-testing system prompts against prompt injections, jailbreaks, and adversarial attacks. FastAPI backend + Streamlit frontend.

## Commands

- **Install:** `uv sync`
- **Add dependency:** `uv add <package>`
- **Backend:** `uv run uvicorn backend.main:app --reload --port 8000`
- **Frontend:** `uv run streamlit run frontend/app.py --server.port 8501`
- **Tests:** `uv run python -m unittest discover -s tests -q`
- **Docker:** `docker-compose up --build`

## Architecture

### Target vs Judge Paradigm

Strictly separate the model under test from the model evaluating the test:

- **Target Model:** User-selected from the UI. Receives `system_prompt` + `attack_text`.
- **Judge Model:** Set via `JUDGE_MODEL` env var (default: `gpt-4.1-mini`). Not changeable from the UI. Returns `{"is_vulnerable": bool, "reason": str}`.

### Rules

- All config lives in `backend/config.py` (Pydantic `BaseSettings`). Access via `get_settings()`. Never call `os.getenv` in business logic.
- Frontend fetches allowed models from `GET /api/v1/models` — backend is the single source of truth.
- Cache key = MD5 of `system_prompt + target_model + temperature + response_format`. Return cached results without calling LLMs.
- Use thread-local SQLite connection pooling — never create connections per request.
- Rate-limit `/api/v1/test-agent` and `/api/v1/custom-payload` via `slowapi`. Limit set by `RATE_LIMIT_PER_DAY` (default 5). Set to 0 to disable.
- `system_prompt` max length: 16000 chars. Reject with HTTP 400.

### Error Handling

- Wrap all LiteLLM calls in `try/except`. Return HTTP 500/502 on upstream failures.
- Raise typed exceptions (`TargetModelError`, `JudgeModelError`, `TelemetryError`) — never return success-shaped fallback payloads.

### Code Conventions

- All LLM calls use `litellm.acompletion` (async). Run concurrent attacks with `asyncio.gather`.
- All `__init__.py` files define `__all__` with explicit exports.
- No logic duplication — each piece of logic exists in exactly one place.

## Directory Structure

```
.
├── .env                          # Environment variables (never commit)
├── .env.example                  # Example env file template
├── pyproject.toml                # Project dependencies
├── uv.lock                       # Lock file
├── docker-compose.yml
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Pydantic Settings (centralized config)
│   ├── dependencies.py           # FastAPI dependencies (limiter, etc.)
│   ├── api/
│   │   ├── router.py             # API endpoints
│   │   └── schemas.py            # Pydantic request/response models
│   ├── core/
│   │   ├── attack_runner.py      # Attack execution logic
│   │   └── evaluator.py          # Judge model evaluation logic
│   ├── services/
│   │   ├── llm_client.py         # Target model LLM calls only
│   │   ├── cache_service.py      # SQLite caching with connection pooling
│   │   ├── telemetry.py          # Usage logging
│   │   ├── errors.py             # Typed service exceptions
│   │   └── test_pipeline.py      # Shared /test-agent orchestration helpers
│   └── data/
│       └── attacks.json          # Attack payload definitions
└── frontend/
    └── app.py                    # Streamlit UI
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `GROQ_API_KEY` | — | Groq API key |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `JUDGE_MODEL` | `gpt-4.1-mini` | Model used for evaluating attacks |
| `RATE_LIMIT_PER_DAY` | `5` | Requests per day per IP (0 = disabled) |
| `BACKEND_URL` | `http://localhost:8000` | Backend URL for frontend |
