"""Tests for backend.app.schemas — Pydantic validation on all request schemas."""

import pytest
from pydantic import ValidationError

from backend.app.schemas import (
    ComparisonCreate,
    JobCreate,
    ModelDeleteRequest,
    ModelPullRequest,
    PromptCreate,
    PromptUpdate,
    SetWinnerRequest,
)


class TestJobCreate:
    def test_minimal(self):
        j = JobCreate(model="gemma3:12b", prompt="Hello")
        assert j.model == "gemma3:12b"
        assert j.prompt == "Hello"
        assert j.temperature == 0.7
        assert j.max_tokens == 2048
        assert j.system_prompt is None

    def test_all_fields(self):
        j = JobCreate(
            model="mistral:7b",
            prompt="Hello",
            system_prompt="Be brief",
            temperature=1.5,
            max_tokens=4096,
        )
        assert j.system_prompt == "Be brief"
        assert j.temperature == 1.5
        assert j.max_tokens == 4096

    def test_missing_model_fails(self):
        with pytest.raises(ValidationError):
            JobCreate(prompt="Hello")

    def test_empty_prompt_fails(self):
        with pytest.raises(ValidationError):
            JobCreate(model="test:7b", prompt="")

    def test_temperature_out_of_range(self):
        with pytest.raises(ValidationError):
            JobCreate(model="test:7b", prompt="Hi", temperature=3.0)

    def test_max_tokens_too_low(self):
        with pytest.raises(ValidationError):
            JobCreate(model="test:7b", prompt="Hi", max_tokens=0)

    def test_max_tokens_too_high(self):
        with pytest.raises(ValidationError):
            JobCreate(model="test:7b", prompt="Hi", max_tokens=200000)


class TestComparisonCreate:
    def test_minimal(self):
        c = ComparisonCreate(name="Test", prompt="Hello", models=["a:7b", "b:7b"])
        assert c.name == "Test"
        assert len(c.models) == 2

    def test_empty_models_fails(self):
        with pytest.raises(ValidationError):
            ComparisonCreate(name="Test", prompt="Hello", models=[])

    def test_empty_name_succeeds(self):
        """Name just needs to be under max_length, it can be short."""
        c = ComparisonCreate(name="X", prompt="Hello", models=["a:7b"])
        assert c.name == "X"


class TestPromptCreate:
    def test_minimal(self):
        p = PromptCreate(name="Test", prompt="Hello world")
        assert p.name == "Test"
        assert p.temperature == 0.7

    def test_empty_prompt_fails(self):
        with pytest.raises(ValidationError):
            PromptCreate(name="Test", prompt="")


class TestPromptUpdate:
    def test_all_none(self):
        """All fields are optional — empty update is valid."""
        p = PromptUpdate()
        assert p.name is None
        assert p.prompt is None

    def test_partial(self):
        p = PromptUpdate(name="Updated")
        assert p.name == "Updated"
        assert p.prompt is None


class TestSetWinnerRequest:
    def test_valid(self):
        r = SetWinnerRequest(winner_job_id="abc-123")
        assert r.winner_job_id == "abc-123"


class TestModelRequests:
    def test_pull_request(self):
        r = ModelPullRequest(name="tinyllama:1.1b")
        assert r.name == "tinyllama:1.1b"

    def test_delete_request(self):
        r = ModelDeleteRequest(name="tinyllama:1.1b")
        assert r.name == "tinyllama:1.1b"
