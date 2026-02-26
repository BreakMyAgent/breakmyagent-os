import asyncio
import logging
from uuid import uuid4

from backend.core.attack_runner import run_all_attacks
from backend.core.evaluator import evaluate_all_results
from backend.services.cache_service import get_cached_result, make_cache_key, store_result
from backend.services.errors import TelemetryError
from backend.services.telemetry import log_test_session

logger = logging.getLogger(__name__)


def get_test_cache_key_and_result(
    system_prompt: str,
    target_model: str,
    temperature: float,
    response_format: str,
) -> tuple[str, dict | None]:
    cache_key = make_cache_key(system_prompt, target_model, temperature, response_format)
    return cache_key, get_cached_result(cache_key)


def build_test_agent_response(target_model: str, evaluated_results: list[dict], run_id: str) -> dict:
    vulnerabilities = sum(1 for result in evaluated_results if result.get("is_vulnerable"))
    return {
        "run_id": run_id,
        "target_model": target_model,
        "total_attacks": len(evaluated_results),
        "vulnerabilities_found": vulnerabilities,
        "results": evaluated_results,
    }


def _schedule_telemetry_log(
    session_id: str,
    system_prompt: str,
    target_model: str,
    response_format: str,
    evaluated_results: list[dict],
) -> None:
    async def _log() -> None:
        try:
            await asyncio.to_thread(
                log_test_session,
                session_id,
                system_prompt,
                target_model,
                response_format,
                evaluated_results,
            )
        except TelemetryError as exc:
            logger.warning("Telemetry logging failed: %s", str(exc))

    asyncio.create_task(_log())


def persist_and_schedule_test_agent_response(
    cache_key: str,
    system_prompt: str,
    target_model: str,
    response_format: str,
    evaluated_results: list[dict],
) -> dict:
    run_id = str(uuid4())
    response_data = build_test_agent_response(target_model, evaluated_results, run_id=run_id)
    has_error_result = any(result.get("error") is not None for result in evaluated_results)
    if not has_error_result:
        store_result(cache_key, response_data)
    _schedule_telemetry_log(run_id, system_prompt, target_model, response_format, evaluated_results)
    return response_data


async def run_test_agent_pipeline(
    system_prompt: str,
    target_model: str,
    temperature: float,
    response_format: str,
) -> dict:
    cache_key, cached = get_test_cache_key_and_result(
        system_prompt=system_prompt,
        target_model=target_model,
        temperature=temperature,
        response_format=response_format,
    )
    if cached is not None:
        return cached

    attack_results = await run_all_attacks(target_model, system_prompt, temperature, response_format)
    evaluated_results = await evaluate_all_results(attack_results)

    return persist_and_schedule_test_agent_response(
        cache_key=cache_key,
        system_prompt=system_prompt,
        target_model=target_model,
        response_format=response_format,
        evaluated_results=evaluated_results,
    )
