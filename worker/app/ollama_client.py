from dataclasses import dataclass

import httpx

from shared.config import settings


@dataclass
class GenerateResult:
    response: str
    input_tokens: int
    output_tokens: int
    generation_time_ms: int


async def generate(
    model: str,
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> GenerateResult:
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system_prompt:
        payload["system"] = system_prompt

    async with httpx.AsyncClient(timeout=600.0) as client:
        resp = await client.post(
            f"{settings.OLLAMA_HOST}/api/generate",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return GenerateResult(
            response=data["response"],
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            # eval_duration is in nanoseconds
            generation_time_ms=int(data.get("eval_duration", 0) / 1_000_000),
        )
