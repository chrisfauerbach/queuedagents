import httpx
from fastapi import APIRouter

from backend.app.schemas import OllamaModelResponse
from shared.config import settings

router = APIRouter()


@router.get("/models", response_model=list[OllamaModelResponse])
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, Exception):
        return []

    models = []
    for m in data.get("models", []):
        details = m.get("details", {})
        models.append(
            OllamaModelResponse(
                name=m["name"],
                size=m.get("size", 0),
                family=details.get("family"),
                parameter_size=details.get("parameter_size"),
                quantization_level=details.get("quantization_level"),
            )
        )
    return models
