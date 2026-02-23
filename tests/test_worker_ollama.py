"""Tests for worker.app.ollama_client — generate() with respx mocks."""

import httpx
import pytest
import respx

from shared.config import settings
from worker.app.ollama_client import GenerateResult, generate

OLLAMA = settings.OLLAMA_HOST


class TestGenerate:
    @respx.mock
    async def test_success(self):
        respx.post(f"{OLLAMA}/api/generate").mock(return_value=httpx.Response(200, json={
            "response": "Hello world!",
            "prompt_eval_count": 10,
            "eval_count": 20,
            "eval_duration": 500_000_000,  # 500ms in nanoseconds
        }))
        result = await generate(model="test:7b", prompt="Hi")
        assert isinstance(result, GenerateResult)
        assert result.response == "Hello world!"
        assert result.input_tokens == 10
        assert result.output_tokens == 20
        assert result.generation_time_ms == 500

    @respx.mock
    async def test_without_system_prompt(self):
        route = respx.post(f"{OLLAMA}/api/generate").mock(
            return_value=httpx.Response(200, json={
                "response": "ok", "prompt_eval_count": 5, "eval_count": 10, "eval_duration": 100_000_000,
            })
        )
        await generate(model="test:7b", prompt="Hi")
        body = route.calls[0].request.content
        import json
        payload = json.loads(body)
        assert "system" not in payload

    @respx.mock
    async def test_with_system_prompt(self):
        route = respx.post(f"{OLLAMA}/api/generate").mock(
            return_value=httpx.Response(200, json={
                "response": "ok", "prompt_eval_count": 5, "eval_count": 10, "eval_duration": 100_000_000,
            })
        )
        await generate(model="test:7b", prompt="Hi", system_prompt="Be helpful")
        import json
        payload = json.loads(route.calls[0].request.content)
        assert payload["system"] == "Be helpful"

    @respx.mock
    async def test_custom_temperature_and_max_tokens(self):
        route = respx.post(f"{OLLAMA}/api/generate").mock(
            return_value=httpx.Response(200, json={
                "response": "ok", "prompt_eval_count": 5, "eval_count": 10, "eval_duration": 100_000_000,
            })
        )
        await generate(model="test:7b", prompt="Hi", temperature=1.5, max_tokens=512)
        import json
        payload = json.loads(route.calls[0].request.content)
        assert payload["options"]["temperature"] == 1.5
        assert payload["options"]["num_predict"] == 512

    @respx.mock
    async def test_missing_eval_fields_default_to_zero(self):
        respx.post(f"{OLLAMA}/api/generate").mock(return_value=httpx.Response(200, json={
            "response": "Hello",
        }))
        result = await generate(model="test:7b", prompt="Hi")
        assert result.input_tokens == 0
        assert result.output_tokens == 0
        assert result.generation_time_ms == 0

    @respx.mock
    async def test_http_error_raises(self):
        respx.post(f"{OLLAMA}/api/generate").mock(return_value=httpx.Response(500))
        with pytest.raises(httpx.HTTPStatusError):
            await generate(model="test:7b", prompt="Hi")

    @respx.mock
    async def test_stream_is_false(self):
        route = respx.post(f"{OLLAMA}/api/generate").mock(
            return_value=httpx.Response(200, json={
                "response": "ok", "prompt_eval_count": 0, "eval_count": 0, "eval_duration": 0,
            })
        )
        await generate(model="test:7b", prompt="Hi")
        import json
        payload = json.loads(route.calls[0].request.content)
        assert payload["stream"] is False
