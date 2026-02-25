import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from backend.config import data_path, get_settings
from backend.services.llm_client import call_target_model
from backend.services.errors import TargetModelError

ATTACKS_PATH = data_path("attacks.json")
settings = get_settings()


def load_attacks() -> list[dict]:
    with open(ATTACKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_single_attack(
    target_model: str, system_prompt: str, attack: dict, temperature: float, response_format: str
) -> dict:
    try:
        response = await call_target_model(
            target_model=target_model,
            system_prompt=system_prompt,
            attack_text=attack["text"],
            temperature=temperature,
            response_format=response_format,
        )
        return {
            "attack_id": attack["id"],
            "attack_name": attack["name"],
            "category": attack["category"],
            "attack_text": attack["text"],
            "system_prompt": system_prompt,
            "target_response": response,
            "error": None,
        }
    except TargetModelError as e:
        return {
            "attack_id": attack["id"],
            "attack_name": attack["name"],
            "category": attack["category"],
            "attack_text": attack["text"],
            "system_prompt": system_prompt,
            "target_response": None,
            "error": str(e),
        }


async def _run_single_attack_with_limit(
    semaphore: asyncio.Semaphore,
    target_model: str,
    system_prompt: str,
    attack: dict,
    temperature: float,
    response_format: str,
) -> dict:
    async with semaphore:
        return await run_single_attack(target_model, system_prompt, attack, temperature, response_format)


async def run_all_attacks(
    target_model: str, system_prompt: str, temperature: float = 0.7, response_format: str = "text"
) -> list[dict]:
    attacks = load_attacks()
    semaphore = asyncio.Semaphore(max(1, settings.max_attack_concurrency))
    tasks = [
        _run_single_attack_with_limit(
            semaphore,
            target_model,
            system_prompt,
            attack,
            temperature,
            response_format,
        )
        for attack in attacks
    ]
    return await asyncio.gather(*tasks)


async def run_all_attacks_with_progress(
    target_model: str, system_prompt: str, temperature: float = 0.7, response_format: str = "text"
) -> AsyncGenerator[dict[str, Any], None]:
    """Run attacks and yield progress updates as each attack completes."""
    attacks = load_attacks()
    total = len(attacks)
    completed = 0
    results: list[dict] = []
    semaphore = asyncio.Semaphore(max(1, settings.max_attack_concurrency))

    tasks = [
        asyncio.create_task(
            _run_single_attack_with_limit(
                semaphore,
                target_model,
                system_prompt,
                attack,
                temperature,
                response_format,
            )
        )
        for attack in attacks
    ]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        completed += 1
        yield {
            "type": "progress",
            "completed": completed,
            "total": total,
            "current_attack": result["attack_name"],
        }

    yield {
        "type": "complete",
        "results": results,
    }
