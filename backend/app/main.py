from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.database import Base, engine
from backend.app.routes.jobs import router as jobs_router
from backend.app.routes.gpu import router as gpu_router
from backend.app.routes.models import router as models_router
from backend.app.routes.comparisons import router as comparisons_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Queued Agents API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router, prefix="/api")
app.include_router(gpu_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(comparisons_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
