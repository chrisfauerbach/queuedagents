"""Tests for /api/jobs, /api/token-usage, /api/stats."""

from datetime import datetime, timedelta, timezone

from shared.models import Job, JobStatus


async def test_create_job(client):
    resp = await client.post("/api/jobs", json={"model": "gemma3:12b", "prompt": "Hello"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["model"] == "gemma3:12b"
    assert data["prompt"] == "Hello"
    assert data["status"] == "pending"
    assert data["id"]


async def test_create_job_all_fields(client):
    resp = await client.post("/api/jobs", json={
        "model": "mistral:7b",
        "prompt": "Hello",
        "system_prompt": "Be brief",
        "temperature": 1.0,
        "max_tokens": 512,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["system_prompt"] == "Be brief"
    assert data["temperature"] == 1.0
    assert data["max_tokens"] == 512


async def test_create_job_invalid_payload(client):
    resp = await client.post("/api/jobs", json={"model": "x"})
    assert resp.status_code == 422


async def test_list_jobs_empty(client):
    resp = await client.get("/api/jobs")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_jobs_returns_jobs(client):
    await client.post("/api/jobs", json={"model": "a:7b", "prompt": "A"})
    await client.post("/api/jobs", json={"model": "b:7b", "prompt": "B"})
    resp = await client.get("/api/jobs")
    assert len(resp.json()) == 2


async def test_list_jobs_filter_by_status(client, session_factory):
    # Create a job then manually set it to completed
    create = await client.post("/api/jobs", json={"model": "a:7b", "prompt": "A"})
    job_id = create.json()["id"]
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one()
        job.status = JobStatus.completed
        await session.commit()

    await client.post("/api/jobs", json={"model": "b:7b", "prompt": "B"})

    resp = await client.get("/api/jobs?status=completed")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "completed"


async def test_list_jobs_limit_offset(client):
    for i in range(5):
        await client.post("/api/jobs", json={"model": f"m{i}:7b", "prompt": f"P{i}"})
    resp = await client.get("/api/jobs?limit=2&offset=0")
    assert len(resp.json()) == 2


async def test_get_job_by_id(client):
    create = await client.post("/api/jobs", json={"model": "a:7b", "prompt": "A"})
    job_id = create.json()["id"]
    resp = await client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


async def test_get_job_404(client):
    resp = await client.get("/api/jobs/nonexistent-id")
    assert resp.status_code == 404


# --- Token usage ---

async def test_token_usage_empty(client):
    resp = await client.get("/api/token-usage")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_token_usage_cumulative(client, session_factory):
    """Token usage should return cumulative per-model running totals."""
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        for i, (inp, out) in enumerate([(10, 20), (30, 40)]):
            job = Job(
                model="test:7b",
                prompt=f"p{i}",
                status=JobStatus.completed,
                input_tokens=inp,
                output_tokens=out,
                completed_at=now + timedelta(seconds=i),
            )
            session.add(job)
        await session.commit()

    resp = await client.get("/api/token-usage?hours=1")
    data = resp.json()
    assert len(data) == 2
    # First point: cumulative 10, 20
    assert data[0]["cumulative_input_tokens"] == 10
    assert data[0]["cumulative_output_tokens"] == 20
    # Second point: cumulative 40, 60
    assert data[1]["cumulative_input_tokens"] == 40
    assert data[1]["cumulative_output_tokens"] == 60
    assert data[1]["job_count"] == 2


async def test_token_usage_excludes_null_tokens(client, session_factory):
    """Jobs with null tokens should not appear in token usage."""
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        session.add(Job(
            model="test:7b", prompt="p", status=JobStatus.completed,
            input_tokens=None, output_tokens=None, completed_at=now,
        ))
        session.add(Job(
            model="test:7b", prompt="q", status=JobStatus.completed,
            input_tokens=5, output_tokens=10, completed_at=now,
        ))
        await session.commit()

    resp = await client.get("/api/token-usage?hours=1")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["cumulative_input_tokens"] == 5


async def test_token_usage_hours_filter(client, session_factory):
    """Jobs outside the hours window should be excluded."""
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        session.add(Job(
            model="test:7b", prompt="old", status=JobStatus.completed,
            input_tokens=100, output_tokens=200,
            completed_at=now - timedelta(hours=48),
        ))
        session.add(Job(
            model="test:7b", prompt="recent", status=JobStatus.completed,
            input_tokens=5, output_tokens=10, completed_at=now,
        ))
        await session.commit()

    resp = await client.get("/api/token-usage?hours=1")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["cumulative_input_tokens"] == 5


# --- Stats ---

async def test_stats_empty(client):
    resp = await client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"pending": 0, "processing": 0, "completed": 0, "failed": 0, "total": 0}


async def test_stats_counts(client, session_factory):
    async with session_factory() as session:
        session.add(Job(model="a:7b", prompt="p", status=JobStatus.pending))
        session.add(Job(model="b:7b", prompt="p", status=JobStatus.pending))
        session.add(Job(model="c:7b", prompt="p", status=JobStatus.completed))
        session.add(Job(model="d:7b", prompt="p", status=JobStatus.failed))
        await session.commit()

    resp = await client.get("/api/stats")
    data = resp.json()
    assert data["pending"] == 2
    assert data["completed"] == 1
    assert data["failed"] == 1
    assert data["total"] == 4
