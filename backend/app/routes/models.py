import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.app.model_catalog import CATALOG
from backend.app.schemas import (
    CatalogModelResponse,
    CatalogVariantResponse,
    ModelDeleteRequest,
    ModelPullRequest,
    ModelShowResponse,
    OllamaModelResponse,
)
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


@router.get("/models/catalog", response_model=list[CatalogModelResponse])
async def get_catalog():
    # Get installed model names
    installed_names: set[str] = set()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            for m in data.get("models", []):
                name = m["name"]
                installed_names.add(name)
                # Also add without :latest suffix
                if name.endswith(":latest"):
                    installed_names.add(name.removesuffix(":latest"))
    except (httpx.HTTPError, Exception):
        pass

    result = []
    for model in CATALOG:
        variants = []
        for v in model.variants:
            full_name = f"{model.name}:{v.tag}"
            installed = full_name in installed_names or f"{full_name}:latest" in installed_names
            variants.append(
                CatalogVariantResponse(
                    tag=v.tag,
                    parameter_size=v.parameter_size,
                    full_name=full_name,
                    installed=installed,
                )
            )
        result.append(
            CatalogModelResponse(
                name=model.name,
                description=model.description,
                category=model.category,
                variants=variants,
            )
        )
    return result


@router.post("/models/pull")
async def pull_model(req: ModelPullRequest):
    async def stream_pull():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{settings.OLLAMA_HOST}/api/pull",
                json={"name": req.name, "stream": True},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield line + "\n"

    return StreamingResponse(stream_pull(), media_type="application/x-ndjson")


@router.post("/models/show", response_model=ModelShowResponse)
async def show_model(req: ModelPullRequest):
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.OLLAMA_HOST}/api/show",
            json={"name": req.name},
        )
        resp.raise_for_status()
        data = resp.json()

    details = data.get("details", {})
    return ModelShowResponse(
        license=data.get("license"),
        modelfile=data.get("modelfile"),
        template=data.get("template"),
        system=data.get("system"),
        parameters=data.get("parameters"),
        family=details.get("family"),
        parameter_size=details.get("parameter_size"),
        quantization_level=details.get("quantization_level"),
    )


@router.delete("/models")
async def delete_model(req: ModelDeleteRequest):
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.request(
            "DELETE",
            f"{settings.OLLAMA_HOST}/api/delete",
            json={"name": req.name},
        )
        resp.raise_for_status()
    return {"status": "deleted", "name": req.name}
