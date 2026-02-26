import litellm

from backend.config import MODEL_TEMPERATURE_OVERRIDES, MODEL_TIMEOUT_OVERRIDES, get_settings
from backend.services.errors import TargetModelError

settings = get_settings()


async def call_target_model(
    target_model: str, system_prompt: str, attack_text: str,
    temperature: float = 0.7, response_format: str = "text",
) -> str:
    """Call the target model with an attack payload."""
    temperature = MODEL_TEMPERATURE_OVERRIDES.get(target_model, temperature)
    timeout = MODEL_TIMEOUT_OVERRIDES.get(target_model, settings.llm_timeout)

    system_content = (
        system_prompt + "\nYou must respond in JSON format."
        if response_format == "json_schema"
        else system_prompt
    )

    kwargs: dict = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": attack_text},
        ],
        "temperature": temperature,
        "timeout": timeout,
    }
    if response_format == "json_schema":
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "agent_reply": {
                            "type": "string",
                            "description": "The actual response or action output of the agent",
                        }
                    },
                    "required": ["agent_reply"],
                    "additionalProperties": False,
                },
            },
        }

    try:
        response = await litellm.acompletion(**kwargs)
    except Exception as exc:
        raise TargetModelError(f"Target model call failed: {str(exc)}") from exc

    content = response.choices[0].message.content
    if content is None:
        raise TargetModelError("Target model returned empty response content.")
    return content
