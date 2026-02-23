"""Shared test fixtures: in-memory DB, async session, FastAPI test client."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.database import Base, get_session

# ---------------------------------------------------------------------------
# Database fixtures (function-scoped → every test gets a clean DB)
# ---------------------------------------------------------------------------

@pytest.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def test_session(session_factory):
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest.fixture
async def client(test_engine, session_factory):
    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from backend.app.routes.jobs import router as jobs_router
    from backend.app.routes.gpu import router as gpu_router
    from backend.app.routes.models import router as models_router
    from backend.app.routes.comparisons import router as comparisons_router
    from backend.app.routes.leaderboard import router as leaderboard_router
    from backend.app.routes.prompts import router as prompts_router

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        # Tables already created by test_engine fixture; skip seed_prompts
        yield

    test_app = FastAPI(lifespan=_lifespan)
    test_app.include_router(jobs_router, prefix="/api")
    test_app.include_router(gpu_router, prefix="/api")
    test_app.include_router(models_router, prefix="/api")
    test_app.include_router(comparisons_router, prefix="/api")
    test_app.include_router(leaderboard_router, prefix="/api")
    test_app.include_router(prompts_router, prefix="/api")

    @test_app.get("/api/health")
    async def health():
        return {"status": "ok"}

    async def _override_session():
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
