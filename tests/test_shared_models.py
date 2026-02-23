"""Tests for shared.models — ORM defaults, relationships, enums."""

import uuid
from datetime import datetime, timezone

from shared.models import Comparison, GpuMetric, Job, JobStatus, Prompt


class TestJobStatus:
    def test_values(self):
        assert set(JobStatus) == {
            JobStatus.pending,
            JobStatus.processing,
            JobStatus.completed,
            JobStatus.failed,
        }

    def test_string_values(self):
        assert JobStatus.pending.value == "pending"
        assert JobStatus.processing.value == "processing"
        assert JobStatus.completed.value == "completed"
        assert JobStatus.failed.value == "failed"


class TestJobModel:
    async def test_defaults(self, test_session):
        job = Job(model="test:7b", prompt="Hello")
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        assert job.id is not None
        uuid.UUID(job.id)  # validates UUID format
        assert job.status == JobStatus.pending
        assert job.temperature == 0.7
        assert job.max_tokens == 2048
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None
        assert job.result is None
        assert job.error is None
        assert job.input_tokens is None
        assert job.output_tokens is None
        assert job.generation_time_ms is None
        assert job.comparison_id is None

    async def test_system_prompt_optional(self, test_session):
        job = Job(model="test:7b", prompt="Hello", system_prompt="Be helpful")
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)
        assert job.system_prompt == "Be helpful"


class TestComparisonModel:
    async def test_defaults(self, test_session):
        comp = Comparison(name="Test", prompt="Hello")
        test_session.add(comp)
        await test_session.commit()
        await test_session.refresh(comp)

        assert comp.id is not None
        uuid.UUID(comp.id)
        assert comp.temperature == 0.7
        assert comp.max_tokens == 2048
        assert comp.winner_job_id is None
        assert comp.created_at is not None

    async def test_jobs_relationship(self, test_session):
        comp = Comparison(name="Test", prompt="Hello")
        test_session.add(comp)
        await test_session.flush()

        job = Job(model="test:7b", prompt="Hello", comparison_id=comp.id)
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(comp)

        assert len(comp.jobs) == 1
        assert comp.jobs[0].model == "test:7b"


class TestPromptModel:
    async def test_defaults(self, test_session):
        p = Prompt(name="Test Prompt", prompt="Hello")
        test_session.add(p)
        await test_session.commit()
        await test_session.refresh(p)

        assert p.id is not None
        uuid.UUID(p.id)
        assert p.temperature == 0.7
        assert p.max_tokens == 2048
        assert p.created_at is not None
        assert p.updated_at is not None


class TestGpuMetricModel:
    async def test_create(self, test_session):
        now = datetime.now(timezone.utc)
        m = GpuMetric(
            gpu_index=0,
            gpu_name="RTX 4090",
            gpu_utilization=85,
            memory_used_mb=8192,
            memory_total_mb=24576,
            temperature_c=72,
            power_watts=320.5,
            recorded_at=now,
        )
        test_session.add(m)
        await test_session.commit()
        await test_session.refresh(m)

        assert m.id is not None
        assert m.gpu_name == "RTX 4090"
        assert m.power_watts == 320.5
