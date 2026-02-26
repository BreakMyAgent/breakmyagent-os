from typing import Literal

from pydantic import BaseModel, Field

from backend.config import ALLOWED_MODELS, get_settings

settings = get_settings()


class TestAgentRequest(BaseModel):
    """Request model for testing an agent against the attack suite."""

    system_prompt: str = Field(..., max_length=settings.max_system_prompt_length)
    target_model: ALLOWED_MODELS
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    response_format: Literal["text", "json_schema"] = "text"


class CustomPayloadRequest(BaseModel):
    """Request model for testing a custom payload against multiple models."""

    system_prompt: str = Field(..., max_length=settings.max_system_prompt_length)
    custom_payload: str = Field(..., max_length=settings.max_custom_payload_length)
    target_models: list[ALLOWED_MODELS] = Field(
        ..., min_length=1, max_length=settings.max_target_models
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    response_format: Literal["text", "json_schema"] = "text"


class AttackResult(BaseModel):
    """Result of a single attack evaluation."""

    attack_id: str
    attack_name: str
    category: str
    attack_text: str
    target_response: str | None
    is_vulnerable: bool
    reason: str


class TestAgentResponse(BaseModel):
    """Response model for test-agent endpoint."""

    run_id: str
    target_model: str
    total_attacks: int
    vulnerabilities_found: int
    results: list[AttackResult]


class SharedResultResponse(BaseModel):
    """Response model for shared results lookup by run_id."""

    run_id: str
    system_prompt: str = ""
    target_model: str
    temperature: float = 0.7
    response_format: str = "text"
    total_attacks: int
    vulnerabilities_found: int
    results: list[AttackResult]


class CustomPayloadResult(BaseModel):
    """Result of a custom payload test against a single model."""

    target_model: str
    target_response: str | None
    is_vulnerable: bool
    reason: str
    error: str | None


class CustomPayloadResponse(BaseModel):
    """Response model for custom-payload endpoint."""

    custom_payload: str
    results: list[CustomPayloadResult]


class WaitlistRequest(BaseModel):
    """Request model for joining the Pro API waitlist."""

    email: str = Field(
        ...,
        min_length=3,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )


class WaitlistResponse(BaseModel):
    """Response model for waitlist submissions."""

    status: str = "ok"
