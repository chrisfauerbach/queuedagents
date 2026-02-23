"""Tests for backend.app.seed — seed_prompts() logic."""

import json
from pathlib import Path

from sqlalchemy import func, select

from shared.models import Prompt


SEED_FILE = Path(__file__).resolve().parent.parent / "backend" / "app" / "seed_prompts.json"


def test_seed_file_exists():
    assert SEED_FILE.is_file()


def test_seed_file_valid_json():
    data = json.loads(SEED_FILE.read_text())
    assert isinstance(data, list)
    assert len(data) > 0


def test_seed_entries_have_required_fields():
    data = json.loads(SEED_FILE.read_text())
    for i, entry in enumerate(data):
        assert "name" in entry, f"Entry {i} missing 'name'"
        assert "prompt" in entry, f"Entry {i} missing 'prompt'"


async def test_seed_prompts_inserts_into_empty_table(session_factory, monkeypatch):
    """seed_prompts should insert rows when the Prompts table is empty."""
    import backend.app.seed as seed_module

    monkeypatch.setattr(seed_module, "async_session", session_factory)
    await seed_module.seed_prompts()

    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(Prompt))
    data = json.loads(SEED_FILE.read_text())
    assert count == len(data)


async def test_seed_prompts_idempotent(session_factory, monkeypatch):
    """Calling seed_prompts twice should not double the rows."""
    import backend.app.seed as seed_module

    monkeypatch.setattr(seed_module, "async_session", session_factory)
    await seed_module.seed_prompts()
    await seed_module.seed_prompts()

    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(Prompt))
    data = json.loads(SEED_FILE.read_text())
    assert count == len(data)
