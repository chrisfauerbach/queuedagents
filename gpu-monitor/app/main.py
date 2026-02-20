import asyncio
import logging
from datetime import datetime, timedelta, timezone

import pynvml
from sqlalchemy import delete

from shared.config import settings
from shared.database import Base, async_session, engine
from shared.models import GpuMetric

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("gpu-monitor")

PRUNE_OLDER_THAN = timedelta(hours=1)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def record_metrics(device_count: int):
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW -> W

        rows.append(
            GpuMetric(
                gpu_index=i,
                gpu_name=name,
                gpu_utilization=util.gpu,
                memory_used_mb=mem.used // (1024 * 1024),
                memory_total_mb=mem.total // (1024 * 1024),
                temperature_c=temp,
                power_watts=round(power, 1),
                recorded_at=now,
            )
        )

    async with async_session() as session:
        session.add_all(rows)
        await session.commit()


async def prune_old_metrics():
    cutoff = datetime.now(timezone.utc) - PRUNE_OLDER_THAN
    async with async_session() as session:
        await session.execute(
            delete(GpuMetric).where(GpuMetric.recorded_at < cutoff)
        )
        await session.commit()


async def main():
    await init_db()

    pynvml.nvmlInit()
    device_count = pynvml.nvmlDeviceGetCount()
    log.info(
        "GPU monitor started: %d GPU(s), polling every %.1fs",
        device_count,
        settings.GPU_POLL_INTERVAL,
    )

    cycle = 0
    try:
        while True:
            try:
                await record_metrics(device_count)
            except Exception:
                log.exception("Error recording GPU metrics")

            # Prune every 30 cycles to avoid doing it every poll
            cycle += 1
            if cycle % 30 == 0:
                try:
                    await prune_old_metrics()
                except Exception:
                    log.exception("Error pruning old metrics")

            await asyncio.sleep(settings.GPU_POLL_INTERVAL)
    finally:
        pynvml.nvmlShutdown()


if __name__ == "__main__":
    asyncio.run(main())
