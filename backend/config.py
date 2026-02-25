import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, get_args

from pydantic_settings import BaseSettings


def data_path(filename: str) -> Path:
    """Return an absolute path to a file inside the project data/ directory.

    Creates the directory if it does not exist.
    """
    path = Path(os.getcwd()) / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


ALLOWED_MODELS = Literal[
    # GPT mini (newest first)
    "gpt-5-mini",
    "gpt-4.1-mini",
    "gpt-4o-mini",
    # GPT standard (newest first)
    "gpt-5.1",
    "gpt-4.1",
    "gpt-4o",
    # Anthropic
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    # DeepSeek
    "openrouter/deepseek/deepseek-chat",
    "openrouter/deepseek/deepseek-reasoner",
    # Qwen (Alibaba)
    "openrouter/qwen/qwen-2.5-72b-instruct",
    "openrouter/qwen/qwen-2.5-coder-32b-instruct",
    # Meta
    "openrouter/meta-llama/llama-3.3-70b-instruct",
    "openrouter/meta-llama/llama-3.1-8b-instruct",
    # Google & Mistral
    "openrouter/google/gemma-2-27b-it",
    "openrouter/mistralai/mistral-nemo",
]

ALLOWED_MODELS_LIST = list(get_args(ALLOWED_MODELS))

# Models that require a fixed temperature regardless of user selection.
MODEL_TEMPERATURE_OVERRIDES: dict[str, float] = {
    "gpt-5-mini": 1.0,
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    judge_model: str = "gpt-4.1-mini"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None

    # Rate Limiting (0 = disabled)
    rate_limit_per_day: int = 5

    # Input Validation Limits
    max_system_prompt_length: int = 16000
    max_custom_payload_length: int = 1000
    max_target_models: int = 3

    # Timeouts
    llm_timeout: int = 15
    
    # Concurrency
    max_attack_concurrency: int = 8
    max_evaluation_concurrency: int = 8

    # CORS
    cors_allow_origins: list[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]
    cors_allow_credentials: bool = False

    @property
    def allowed_models(self) -> list[str]:
        """Return the full list of supported target models."""
        return list(ALLOWED_MODELS_LIST)

    @property
    def available_models(self) -> list[str]:
        """Return only models whose provider API key is configured."""
        result = []
        for model in ALLOWED_MODELS_LIST:
            if model.startswith("gpt-") and self.openai_api_key:
                result.append(model)
            elif model.startswith("claude-") and self.anthropic_api_key:
                result.append(model)
            elif model.startswith("openrouter/") and self.openrouter_api_key:
                result.append(model)
            elif model.startswith("groq/") and self.groq_api_key:
                result.append(model)
        return result

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
