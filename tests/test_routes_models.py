"""Tests for /api/models — Ollama proxying via respx mocks."""

import json

import httpx
import respx

from shared.config import settings


OLLAMA = settings.OLLAMA_HOST


class TestListModels:
    @respx.mock
    async def test_success(self, client):
        respx.get(f"{OLLAMA}/api/tags").mock(return_value=httpx.Response(200, json={
            "models": [
                {"name": "gemma3:12b", "size": 1234, "details": {"family": "gemma", "parameter_size": "12B"}},
            ],
        }))
        resp = await client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "gemma3:12b"
        assert data[0]["family"] == "gemma"

    @respx.mock
    async def test_ollama_unreachable(self, client):
        respx.get(f"{OLLAMA}/api/tags").mock(side_effect=httpx.ConnectError("refused"))
        resp = await client.get("/api/models")
        assert resp.status_code == 200
        assert resp.json() == []


class TestCatalog:
    @respx.mock
    async def test_no_installed_models(self, client):
        respx.get(f"{OLLAMA}/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
        resp = await client.get("/api/models/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        # All variants should be not installed
        for model in data:
            for v in model["variants"]:
                assert v["installed"] is False

    @respx.mock
    async def test_with_installed_model(self, client):
        respx.get(f"{OLLAMA}/api/tags").mock(return_value=httpx.Response(200, json={
            "models": [{"name": "mistral:7b", "size": 1000, "details": {}}],
        }))
        resp = await client.get("/api/models/catalog")
        data = resp.json()
        mistral = next(m for m in data if m["name"] == "mistral")
        variant_7b = next(v for v in mistral["variants"] if v["tag"] == "7b")
        assert variant_7b["installed"] is True

    @respx.mock
    async def test_with_latest_suffix(self, client):
        respx.get(f"{OLLAMA}/api/tags").mock(return_value=httpx.Response(200, json={
            "models": [{"name": "mistral:7b:latest", "size": 1000, "details": {}}],
        }))
        resp = await client.get("/api/models/catalog")
        # Should still work — the code handles :latest suffix stripping
        assert resp.status_code == 200

    @respx.mock
    async def test_ollama_error(self, client):
        respx.get(f"{OLLAMA}/api/tags").mock(return_value=httpx.Response(500))
        resp = await client.get("/api/models/catalog")
        assert resp.status_code == 200
        data = resp.json()
        # All should be not installed since we couldn't reach Ollama
        for model in data:
            for v in model["variants"]:
                assert v["installed"] is False


class TestShowModel:
    @respx.mock
    async def test_success(self, client):
        respx.post(f"{OLLAMA}/api/show").mock(return_value=httpx.Response(200, json={
            "license": "MIT",
            "modelfile": "FROM gemma",
            "template": "{{.Prompt}}",
            "system": "You are helpful.",
            "parameters": "stop <|im_end|>",
            "details": {"family": "gemma", "parameter_size": "12B", "quantization_level": "Q4_K_M"},
        }))
        resp = await client.post("/api/models/show", json={"name": "gemma3:12b"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["license"] == "MIT"
        assert data["family"] == "gemma"

    @respx.mock
    async def test_ollama_error(self, client):
        respx.post(f"{OLLAMA}/api/show").mock(return_value=httpx.Response(404))
        resp = await client.post("/api/models/show", json={"name": "nonexistent"})
        assert resp.status_code == 500  # httpx raises, FastAPI returns 500


class TestDeleteModel:
    @respx.mock
    async def test_success(self, client):
        respx.delete(f"{OLLAMA}/api/delete").mock(return_value=httpx.Response(200))
        resp = await client.request("DELETE", "/api/models", json={"name": "tinyllama:1.1b"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    @respx.mock
    async def test_ollama_error(self, client):
        respx.delete(f"{OLLAMA}/api/delete").mock(return_value=httpx.Response(404))
        resp = await client.request("DELETE", "/api/models", json={"name": "nonexistent"})
        assert resp.status_code == 500
