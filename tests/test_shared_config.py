"""Tests for shared.config — Settings defaults and env overrides."""

import os

import pytest


def test_defaults():
    """Settings should have sensible defaults without any env vars."""
    from shared.config import Settings

    s = Settings()
    assert s.DATABASE_URL == "sqlite+aiosqlite:///./data/queue.db"
    assert s.OLLAMA_HOST == "http://ollama:11434"
    assert s.POLL_INTERVAL == 1.0
    assert s.GPU_POLL_INTERVAL == 2.0


def test_env_override_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    from shared.config import Settings

    s = Settings()
    assert s.DATABASE_URL == "sqlite+aiosqlite:///./test.db"


def test_env_override_ollama_host(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    from shared.config import Settings

    s = Settings()
    assert s.OLLAMA_HOST == "http://localhost:11434"


def test_env_override_poll_interval(monkeypatch):
    monkeypatch.setenv("POLL_INTERVAL", "5.0")
    from shared.config import Settings

    s = Settings()
    assert s.POLL_INTERVAL == 5.0


def test_env_override_gpu_poll_interval(monkeypatch):
    monkeypatch.setenv("GPU_POLL_INTERVAL", "10.0")
    from shared.config import Settings

    s = Settings()
    assert s.GPU_POLL_INTERVAL == 10.0


def test_extra_env_ignored(monkeypatch):
    """Extra environment variables should not cause errors (extra='ignore')."""
    monkeypatch.setenv("TOTALLY_UNKNOWN_VAR", "whatever")
    from shared.config import Settings

    s = Settings()
    assert not hasattr(s, "TOTALLY_UNKNOWN_VAR")
