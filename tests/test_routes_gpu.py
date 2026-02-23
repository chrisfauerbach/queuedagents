"""Tests for /api/gpu/metrics — metrics query with time filtering."""

from datetime import datetime, timedelta, timezone

from shared.models import GpuMetric


async def test_gpu_metrics_empty(client):
    resp = await client.get("/api/gpu/metrics")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_gpu_metrics_returns_recent(client, session_factory):
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        session.add(GpuMetric(
            gpu_index=0, gpu_name="RTX 4090", gpu_utilization=80,
            memory_used_mb=8000, memory_total_mb=24000,
            temperature_c=70, power_watts=300.0, recorded_at=now,
        ))
        await session.commit()

    resp = await client.get("/api/gpu/metrics?minutes=10")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["gpu_name"] == "RTX 4090"


async def test_gpu_metrics_excludes_old(client, session_factory):
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        session.add(GpuMetric(
            gpu_index=0, gpu_name="Old GPU", gpu_utilization=50,
            memory_used_mb=4000, memory_total_mb=12000,
            temperature_c=60, power_watts=200.0,
            recorded_at=now - timedelta(hours=2),
        ))
        session.add(GpuMetric(
            gpu_index=0, gpu_name="New GPU", gpu_utilization=90,
            memory_used_mb=8000, memory_total_mb=24000,
            temperature_c=75, power_watts=350.0, recorded_at=now,
        ))
        await session.commit()

    resp = await client.get("/api/gpu/metrics?minutes=10")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["gpu_name"] == "New GPU"


async def test_gpu_metrics_ordered_by_time(client, session_factory):
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        for i in range(3):
            session.add(GpuMetric(
                gpu_index=0, gpu_name=f"GPU-{i}", gpu_utilization=50 + i * 10,
                memory_used_mb=4000, memory_total_mb=12000,
                temperature_c=60, power_watts=200.0,
                recorded_at=now - timedelta(seconds=30 * (2 - i)),
            ))
        await session.commit()

    resp = await client.get("/api/gpu/metrics?minutes=10")
    data = resp.json()
    assert len(data) == 3
    # Should be ascending by recorded_at
    assert data[0]["gpu_name"] == "GPU-0"
    assert data[2]["gpu_name"] == "GPU-2"


async def test_gpu_metrics_minutes_param_validation(client):
    resp = await client.get("/api/gpu/metrics?minutes=0")
    assert resp.status_code == 422
    resp = await client.get("/api/gpu/metrics?minutes=61")
    assert resp.status_code == 422
