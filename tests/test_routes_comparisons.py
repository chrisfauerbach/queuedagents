"""Tests for /api/comparisons — CRUD, set/clear winner with validation."""

from shared.models import Job, JobStatus


async def test_create_comparison(client):
    resp = await client.post("/api/comparisons", json={
        "name": "Test Battle",
        "prompt": "Hello",
        "models": ["mistral:7b", "gemma3:12b"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Battle"
    assert data["prompt"] == "Hello"
    assert len(data["jobs"]) == 2
    models = {j["model"] for j in data["jobs"]}
    assert models == {"mistral:7b", "gemma3:12b"}
    for j in data["jobs"]:
        assert j["status"] == "pending"


async def test_create_comparison_with_optional_fields(client):
    resp = await client.post("/api/comparisons", json={
        "name": "Battle",
        "prompt": "Explain X",
        "models": ["a:7b"],
        "system_prompt": "Be brief",
        "temperature": 0.3,
        "max_tokens": 512,
    })
    data = resp.json()
    assert data["system_prompt"] == "Be brief"
    assert data["temperature"] == 0.3
    assert data["max_tokens"] == 512
    # The spawned job should inherit these params
    assert data["jobs"][0]["temperature"] == 0.3


async def test_list_comparisons_empty(client):
    resp = await client.get("/api/comparisons")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_comparisons_ordered_desc(client):
    await client.post("/api/comparisons", json={"name": "First", "prompt": "A", "models": ["a:7b"]})
    await client.post("/api/comparisons", json={"name": "Second", "prompt": "B", "models": ["b:7b"]})
    resp = await client.get("/api/comparisons")
    data = resp.json()
    assert len(data) == 2
    # Most recent first
    assert data[0]["name"] == "Second"


async def test_get_comparison_by_id(client):
    create = await client.post("/api/comparisons", json={
        "name": "X", "prompt": "Y", "models": ["a:7b"],
    })
    cid = create.json()["id"]
    resp = await client.get(f"/api/comparisons/{cid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == cid


async def test_get_comparison_404(client):
    resp = await client.get("/api/comparisons/nonexistent")
    assert resp.status_code == 404


async def test_set_winner_success(client, session_factory):
    # Create comparison with 2 models
    create = await client.post("/api/comparisons", json={
        "name": "Battle", "prompt": "Hi", "models": ["a:7b", "b:7b"],
    })
    cid = create.json()["id"]
    jobs = create.json()["jobs"]
    winner_id = jobs[0]["id"]

    # Mark the job as completed
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Job).where(Job.id == winner_id))
        job = res.scalar_one()
        job.status = JobStatus.completed
        await session.commit()

    resp = await client.put(f"/api/comparisons/{cid}/winner", json={"winner_job_id": winner_id})
    assert resp.status_code == 200
    assert resp.json()["winner_job_id"] == winner_id


async def test_set_winner_comparison_404(client):
    resp = await client.put("/api/comparisons/nonexistent/winner", json={"winner_job_id": "abc"})
    assert resp.status_code == 404


async def test_set_winner_job_not_in_comparison(client, session_factory):
    create = await client.post("/api/comparisons", json={
        "name": "Battle", "prompt": "Hi", "models": ["a:7b"],
    })
    cid = create.json()["id"]

    # Create a separate job not in this comparison
    create2 = await client.post("/api/jobs", json={"model": "x:7b", "prompt": "X"})
    other_job_id = create2.json()["id"]

    resp = await client.put(f"/api/comparisons/{cid}/winner", json={"winner_job_id": other_job_id})
    assert resp.status_code == 404


async def test_set_winner_job_not_completed(client):
    create = await client.post("/api/comparisons", json={
        "name": "Battle", "prompt": "Hi", "models": ["a:7b"],
    })
    cid = create.json()["id"]
    job_id = create.json()["jobs"][0]["id"]

    # Job is still pending — should fail
    resp = await client.put(f"/api/comparisons/{cid}/winner", json={"winner_job_id": job_id})
    assert resp.status_code == 400


async def test_clear_winner_success(client, session_factory):
    create = await client.post("/api/comparisons", json={
        "name": "Battle", "prompt": "Hi", "models": ["a:7b"],
    })
    cid = create.json()["id"]
    job_id = create.json()["jobs"][0]["id"]

    # Complete job, set winner, then clear
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one()
        job.status = JobStatus.completed
        await session.commit()

    await client.put(f"/api/comparisons/{cid}/winner", json={"winner_job_id": job_id})
    resp = await client.delete(f"/api/comparisons/{cid}/winner")
    assert resp.status_code == 200
    assert resp.json()["winner_job_id"] is None


async def test_clear_winner_404(client):
    resp = await client.delete("/api/comparisons/nonexistent/winner")
    assert resp.status_code == 404
