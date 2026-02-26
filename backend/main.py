from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from backend.api.router import router
from backend.api.schemas import WaitlistRequest, WaitlistResponse
from backend.config import MODEL_TEMPERATURE_OVERRIDES, get_settings
from backend.dependencies import limiter
from backend.services.errors import TelemetryError
from backend.services.telemetry import add_waitlist_lead

settings = get_settings()

app = FastAPI(
    title="BreakMyAgent",
    description="AI Agent Safety Sandbox - Stress-test system prompts against adversarial attacks",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "daily_limit": settings.rate_limit_per_day,
        },
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/models")
async def list_models() -> dict:
    """Return only models whose provider API key is configured."""
    return {
        "models": settings.available_models,
        "temperature_overrides": MODEL_TEMPERATURE_OVERRIDES,
    }


@app.post("/api/waitlist", response_model=WaitlistResponse)
async def join_waitlist(body: WaitlistRequest) -> dict:
    try:
        add_waitlist_lead(body.email)
    except TelemetryError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save waitlist lead: {str(exc)}") from exc
    return {"status": "ok"}
