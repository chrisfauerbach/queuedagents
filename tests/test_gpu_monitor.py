"""Tests for gpu_monitor.app.main — record/prune metrics with mocked pynvml."""

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy import func, select

from shared.models import GpuMetric


async def test_record_metrics_single_gpu(session_factory, test_engine, monkeypatch):
    import gpu_monitor.app.main as gm

    monkeypatch.setattr(gm, "async_session", session_factory)
    monkeypatch.setattr(gm, "engine", test_engine)

    mock_pynvml = MagicMock()
    mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = "handle0"
    mock_pynvml.nvmlDeviceGetName.return_value = "RTX 4090"
    mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = SimpleNamespace(gpu=85, memory=60)
    mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = SimpleNamespace(
        used=8 * 1024 * 1024 * 1024,  # 8 GB in bytes
        total=24 * 1024 * 1024 * 1024,  # 24 GB in bytes
    )
    mock_pynvml.nvmlDeviceGetTemperature.return_value = 72
    mock_pynvml.NVML_TEMPERATURE_GPU = 0
    mock_pynvml.nvmlDeviceGetPowerUsage.return_value = 320500  # milliwatts

    monkeypatch.setattr(gm, "pynvml", mock_pynvml)

    await gm.record_metrics(device_count=1)

    async with session_factory() as session:
        result = await session.execute(select(GpuMetric))
        rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].gpu_name == "RTX 4090"
    assert rows[0].gpu_utilization == 85
    assert rows[0].memory_used_mb == 8192
    assert rows[0].memory_total_mb == 24576
    assert rows[0].temperature_c == 72
    assert rows[0].power_watts == 320.5


async def test_record_metrics_multiple_gpus(session_factory, test_engine, monkeypatch):
    import gpu_monitor.app.main as gm

    monkeypatch.setattr(gm, "async_session", session_factory)
    monkeypatch.setattr(gm, "engine", test_engine)

    mock_pynvml = MagicMock()
    mock_pynvml.nvmlDeviceGetHandleByIndex.side_effect = lambda i: f"handle{i}"
    mock_pynvml.nvmlDeviceGetName.side_effect = lambda h: f"GPU-{h}"
    mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = SimpleNamespace(gpu=50, memory=40)
    mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = SimpleNamespace(
        used=4 * 1024 * 1024 * 1024, total=12 * 1024 * 1024 * 1024,
    )
    mock_pynvml.nvmlDeviceGetTemperature.return_value = 65
    mock_pynvml.NVML_TEMPERATURE_GPU = 0
    mock_pynvml.nvmlDeviceGetPowerUsage.return_value = 200000

    monkeypatch.setattr(gm, "pynvml", mock_pynvml)

    await gm.record_metrics(device_count=3)

    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(GpuMetric))
    assert count == 3


async def test_prune_old_metrics(session_factory, test_engine, monkeypatch):
    import gpu_monitor.app.main as gm

    monkeypatch.setattr(gm, "async_session", session_factory)
    monkeypatch.setattr(gm, "engine", test_engine)

    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        # Old metric (should be pruned)
        session.add(GpuMetric(
            gpu_index=0, gpu_name="Old", gpu_utilization=50,
            memory_used_mb=4000, memory_total_mb=12000,
            temperature_c=60, power_watts=200.0,
            recorded_at=now - timedelta(hours=2),
        ))
        # Recent metric (should remain)
        session.add(GpuMetric(
            gpu_index=0, gpu_name="New", gpu_utilization=80,
            memory_used_mb=8000, memory_total_mb=24000,
            temperature_c=70, power_watts=300.0,
            recorded_at=now,
        ))
        await session.commit()

    await gm.prune_old_metrics()

    async with session_factory() as session:
        result = await session.execute(select(GpuMetric))
        rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].gpu_name == "New"


async def test_prune_keeps_recent(session_factory, test_engine, monkeypatch):
    import gpu_monitor.app.main as gm

    monkeypatch.setattr(gm, "async_session", session_factory)
    monkeypatch.setattr(gm, "engine", test_engine)

    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        session.add(GpuMetric(
            gpu_index=0, gpu_name="Recent", gpu_utilization=50,
            memory_used_mb=4000, memory_total_mb=12000,
            temperature_c=60, power_watts=200.0,
            recorded_at=now - timedelta(minutes=30),
        ))
        await session.commit()

    await gm.prune_old_metrics()

    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(GpuMetric))
    assert count == 1


async def test_main_loop_calls_record_and_prune(session_factory, test_engine, monkeypatch):
    import gpu_monitor.app.main as gm

    monkeypatch.setattr(gm, "async_session", session_factory)
    monkeypatch.setattr(gm, "engine", test_engine)

    mock_pynvml = MagicMock()
    mock_pynvml.nvmlDeviceGetCount.return_value = 1
    mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = "handle"
    mock_pynvml.nvmlDeviceGetName.return_value = "GPU-0"
    mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = SimpleNamespace(gpu=50, memory=40)
    mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = SimpleNamespace(
        used=4 * 1024**3, total=12 * 1024**3,
    )
    mock_pynvml.nvmlDeviceGetTemperature.return_value = 65
    mock_pynvml.NVML_TEMPERATURE_GPU = 0
    mock_pynvml.nvmlDeviceGetPowerUsage.return_value = 200000
    monkeypatch.setattr(gm, "pynvml", mock_pynvml)

    call_count = 0

    async def mock_sleep(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise KeyboardInterrupt("Stop loop")

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    try:
        await gm.main()
    except KeyboardInterrupt:
        pass

    mock_pynvml.nvmlInit.assert_called_once()
    mock_pynvml.nvmlShutdown.assert_called_once()
    assert call_count >= 2

    # Verify metrics were recorded
    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(GpuMetric))
    assert count >= 1


async def test_main_loop_handles_record_exception(session_factory, test_engine, monkeypatch):
    """record_metrics exception should not crash the loop."""
    import gpu_monitor.app.main as gm

    monkeypatch.setattr(gm, "async_session", session_factory)
    monkeypatch.setattr(gm, "engine", test_engine)

    mock_pynvml = MagicMock()
    mock_pynvml.nvmlDeviceGetCount.return_value = 1
    # Make record_metrics fail by having the handle call raise
    mock_pynvml.nvmlDeviceGetHandleByIndex.side_effect = RuntimeError("GPU not found")
    monkeypatch.setattr(gm, "pynvml", mock_pynvml)

    call_count = 0

    async def mock_sleep(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            raise KeyboardInterrupt("Stop loop")

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    try:
        await gm.main()
    except KeyboardInterrupt:
        pass

    # Loop should have continued despite the exception
    assert call_count >= 1
    mock_pynvml.nvmlShutdown.assert_called_once()


async def test_main_prunes_on_30th_cycle(session_factory, test_engine, monkeypatch):
    """Pruning should happen every 30 cycles."""
    import gpu_monitor.app.main as gm

    monkeypatch.setattr(gm, "async_session", session_factory)
    monkeypatch.setattr(gm, "engine", test_engine)

    mock_pynvml = MagicMock()
    mock_pynvml.nvmlDeviceGetCount.return_value = 1
    mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = "handle"
    mock_pynvml.nvmlDeviceGetName.return_value = "GPU-0"
    mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = SimpleNamespace(gpu=50, memory=40)
    mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = SimpleNamespace(
        used=4 * 1024**3, total=12 * 1024**3,
    )
    mock_pynvml.nvmlDeviceGetTemperature.return_value = 65
    mock_pynvml.NVML_TEMPERATURE_GPU = 0
    mock_pynvml.nvmlDeviceGetPowerUsage.return_value = 200000
    monkeypatch.setattr(gm, "pynvml", mock_pynvml)

    prune_called = False
    original_prune = gm.prune_old_metrics

    async def mock_prune():
        nonlocal prune_called
        prune_called = True

    monkeypatch.setattr(gm, "prune_old_metrics", mock_prune)

    cycle = 0

    async def mock_sleep(delay):
        nonlocal cycle
        cycle += 1
        if cycle >= 31:
            raise KeyboardInterrupt("Stop")

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    try:
        await gm.main()
    except KeyboardInterrupt:
        pass

    assert prune_called is True
