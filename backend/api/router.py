import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.api.schemas import (
    CustomPayloadRequest,
    CustomPayloadResponse,
    TestAgentRequest,
    TestAgentResponse,
)
from backend.core.attack_runner import run_all_attacks_with_progress
from backend.core.evaluator import evaluate_attack, evaluate_single_result
from backend.dependencies import ATTACK_RATE_LIMIT_SCOPE, RATE_LIMIT, limiter
from backend.services.errors import JudgeModelError, TargetModelError
from backend.services.llm_client import call_target_model
from backend.services.test_pipeline import (
    get_test_cache_key_and_result,
    persist_and_schedule_test_agent_response,
    run_test_agent_pipeline,
)

router = APIRouter(prefix="/api/v1")


@router.post("/test-agent", response_model=TestAgentResponse)
@limiter.shared_limit(RATE_LIMIT, scope=ATTACK_RATE_LIMIT_SCOPE)
async def test_agent(request: Request, body: TestAgentRequest) -> dict:
    try:
        return await run_test_agent_pipeline(
            body.system_prompt,
            body.target_model,
            body.temperature,
            body.response_format,
        )
    except TargetModelError as exc:
        raise HTTPException(status_code=502, detail=f"Target model call failed: {str(exc)}") from exc
    except JudgeModelError as exc:
        raise HTTPException(status_code=502, detail=f"Judge evaluation failed: {str(exc)}") from exc


@router.post("/test-agent/stream")
@limiter.shared_limit(RATE_LIMIT, scope=ATTACK_RATE_LIMIT_SCOPE)
async def test_agent_stream(request: Request, body: TestAgentRequest) -> StreamingResponse:
    """Stream progress updates as attacks are executed and evaluated."""
    cache_key, cached = get_test_cache_key_and_result(
        body.system_prompt, body.target_model, body.temperature, body.response_format
    )
    if cached is not None:
        async def cached_generator():
            yield f"data: {json.dumps({'type': 'cached', 'data': cached})}\n\n"
        return StreamingResponse(cached_generator(), media_type="text/event-stream")

    async def event_generator():
        results: list[dict] = []

        try:
            async for update in run_all_attacks_with_progress(
                body.target_model, body.system_prompt, body.temperature, body.response_format
            ):
                if update["type"] == "progress":
                    yield f"data: {json.dumps({'type': 'attack_progress', 'completed': update['completed'], 'total': update['total'], 'current_attack': update['current_attack']})}\n\n"
                elif update["type"] == "complete":
                    results = update["results"]

            # Now evaluate results with progress
            evaluated: list[dict] = []
            for i, result in enumerate(results):
                eval_result = await evaluate_single_result(result.copy())
                evaluated.append(eval_result)
                yield f"data: {json.dumps({'type': 'eval_progress', 'completed': i + 1, 'total': len(results), 'current_attack': result['attack_name']})}\n\n"

            response_data = persist_and_schedule_test_agent_response(
                cache_key=cache_key,
                system_prompt=body.system_prompt,
                target_model=body.target_model,
                response_format=body.response_format,
                evaluated_results=evaluated,
            )

            yield f"data: {json.dumps({'type': 'complete', 'data': response_data})}\n\n"

        except (TargetModelError, JudgeModelError) as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def _run_custom_payload_for_model(
    target_model: str,
    system_prompt: str,
    custom_payload: str,
    temperature: float,
    response_format: str,
) -> dict:
    """Run a custom payload against a single model and evaluate the result."""
    try:
        target_response = await call_target_model(
            target_model=target_model,
            system_prompt=system_prompt,
            attack_text=custom_payload,
            temperature=temperature,
            response_format=response_format,
        )
    except TargetModelError as exc:
        return {
            "target_model": target_model,
            "target_response": None,
            "is_vulnerable": False,
            "reason": f"Target model call failed: {str(exc)}",
            "error": str(exc),
        }

    try:
        judgement = await evaluate_attack(
            system_prompt=system_prompt,
            attack_text=custom_payload,
            agent_response=target_response,
        )
        return {
            "target_model": target_model,
            "target_response": target_response,
            "is_vulnerable": judgement["is_vulnerable"],
            "reason": judgement["reason"],
            "error": None,
        }
    except JudgeModelError as exc:
        return {
            "target_model": target_model,
            "target_response": target_response,
            "is_vulnerable": False,
            "reason": f"Judge evaluation failed: {str(exc)}",
            "error": str(exc),
        }


@router.post("/custom-payload", response_model=CustomPayloadResponse)
@limiter.shared_limit(RATE_LIMIT, scope=ATTACK_RATE_LIMIT_SCOPE)
async def test_custom_payload(request: Request, body: CustomPayloadRequest) -> dict:
    """Test a custom payload against multiple target models concurrently."""
    tasks = [
        _run_custom_payload_for_model(
            target_model=model,
            system_prompt=body.system_prompt,
            custom_payload=body.custom_payload,
            temperature=body.temperature,
            response_format=body.response_format,
        )
        for model in body.target_models
    ]
    results = await asyncio.gather(*tasks)

    return {
        "custom_payload": body.custom_payload,
        "results": results,
    }
