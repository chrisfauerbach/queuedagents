"""Tests for shared.database — Base, get_session, WAL pragma."""

from shared.database import Base, get_session


def test_base_has_metadata():
    """Base should be a valid SQLAlchemy DeclarativeBase."""
    assert hasattr(Base, "metadata")
    assert "jobs" in Base.metadata.tables
    assert "comparisons" in Base.metadata.tables
    assert "prompts" in Base.metadata.tables
    assert "gpu_metrics" in Base.metadata.tables


async def test_get_session_yields_session():
    """get_session should be an async generator (FastAPI dependency)."""
    import inspect

    assert inspect.isasyncgenfunction(get_session)


async def test_in_memory_engine_works(test_engine):
    """The test engine should support create_all / drop_all."""
    from sqlalchemy import text

    async with test_engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = {row[0] for row in result.all()}
    assert "jobs" in tables
    assert "comparisons" in tables
