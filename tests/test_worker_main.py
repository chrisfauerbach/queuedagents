"""Tests for worker.app.main — claim/complete/fail/process_job and main loop."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from sqlalchemy import select

from shared.models import Job, JobStatus
from worker.app.ollama_client import GenerateResult


async def test_claim_job_returns_oldest_pending(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    async with session_factory() as session:
        session.add(Job(model="first:7b", prompt="A", status=JobStatus.pending))
        session.add(Job(model="second:7b", prompt="B", status=JobStatus.pending))
        await session.commit()

    job = await worker_main.claim_job()
    assert job is not None
    assert job.model == "first:7b"
    assert job.status == JobStatus.processing
    assert job.started_at is not None


async def test_claim_job_returns_none_when_empty(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    job = await worker_main.claim_job()
    assert job is None


async def test_claim_job_skips_non_pending(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    async with session_factory() as session:
        session.add(Job(model="a:7b", prompt="p", status=JobStatus.processing))
        session.add(Job(model="b:7b", prompt="p", status=JobStatus.completed))
        session.add(Job(model="c:7b", prompt="p", status=JobStatus.failed))
        await session.commit()

    job = await worker_main.claim_job()
    assert job is None


async def test_complete_job(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    async with session_factory() as session:
        job = Job(model="test:7b", prompt="p", status=JobStatus.processing)
        session.add(job)
        await session.commit()
        job_id = job.id

    await worker_main.complete_job(job_id, result="Hello!", input_tokens=10, output_tokens=20, generation_time_ms=500)

    async with session_factory() as session:
        res = await session.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one()
    assert job.status == JobStatus.completed
    assert job.result == "Hello!"
    assert job.input_tokens == 10
    assert job.output_tokens == 20
    assert job.generation_time_ms == 500
    assert job.completed_at is not None


async def test_fail_job(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    async with session_factory() as session:
        job = Job(model="test:7b", prompt="p", status=JobStatus.processing)
        session.add(job)
        await session.commit()
        job_id = job.id

    await worker_main.fail_job(job_id, error="Connection refused")

    async with session_factory() as session:
        res = await session.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one()
    assert job.status == JobStatus.failed
    assert job.error == "Connection refused"
    assert job.completed_at is not None


async def test_process_job_success(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    mock_generate = AsyncMock(return_value=GenerateResult(
        response="Hello!", input_tokens=10, output_tokens=20, generation_time_ms=500,
    ))
    monkeypatch.setattr(worker_main, "generate", mock_generate)

    async with session_factory() as session:
        job = Job(model="test:7b", prompt="p", status=JobStatus.processing)
        session.add(job)
        await session.commit()
        await session.refresh(job)

    await worker_main.process_job(job)

    async with session_factory() as session:
        res = await session.execute(select(Job).where(Job.id == job.id))
        updated = res.scalar_one()
    assert updated.status == JobStatus.completed
    assert updated.result == "Hello!"
    mock_generate.assert_called_once()


async def test_process_job_failure(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    mock_generate = AsyncMock(side_effect=RuntimeError("Ollama down"))
    monkeypatch.setattr(worker_main, "generate", mock_generate)

    async with session_factory() as session:
        job = Job(model="test:7b", prompt="p", status=JobStatus.processing)
        session.add(job)
        await session.commit()
        await session.refresh(job)

    await worker_main.process_job(job)

    async with session_factory() as session:
        res = await session.execute(select(Job).where(Job.id == job.id))
        updated = res.scalar_one()
    assert updated.status == JobStatus.failed
    assert "RuntimeError" in updated.error


async def test_main_loop_processes_then_sleeps(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    mock_generate = AsyncMock(return_value=GenerateResult(
        response="ok", input_tokens=1, output_tokens=1, generation_time_ms=100,
    ))
    monkeypatch.setattr(worker_main, "generate", mock_generate)

    async with session_factory() as session:
        session.add(Job(model="test:7b", prompt="p", status=JobStatus.pending))
        await session.commit()

    call_count = 0
    original_sleep = asyncio.sleep

    async def mock_sleep(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            raise KeyboardInterrupt("Stop loop")

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    try:
        await worker_main.main()
    except KeyboardInterrupt:
        pass

    # The job should have been processed before sleep was called
    mock_generate.assert_called_once()
    assert call_count >= 1


async def test_main_loop_sleeps_when_no_job(session_factory, monkeypatch):
    import worker.app.main as worker_main

    monkeypatch.setattr(worker_main, "async_session", session_factory)

    call_count = 0

    async def mock_sleep(delay):
        nonlocal call_count
        call_count += 1
        raise KeyboardInterrupt("Stop loop")

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    try:
        await worker_main.main()
    except KeyboardInterrupt:
        pass

    assert call_count == 1
