"""External service integrations (LLM, cache, telemetry)."""

from backend.services.cache_service import (
    get_cached_result,
    make_cache_key,
    store_result,
)
from backend.services.errors import (
    JudgeModelError,
    TargetModelError,
    TelemetryError,
    UpstreamServiceError,
)
from backend.services.llm_client import call_target_model
from backend.services.telemetry import (
    add_waitlist_lead,
    generate_session_id,
    log_test_session,
)

__all__ = [
    "call_target_model",
    "get_cached_result",
    "make_cache_key",
    "store_result",
    "UpstreamServiceError",
    "TargetModelError",
    "JudgeModelError",
    "TelemetryError",
    "add_waitlist_lead",
    "generate_session_id",
    "log_test_session",
]
