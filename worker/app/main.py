import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from shared.config import settings
from shared.database import async_session
from shared.models import Job, JobStatus
from worker.app.ollama_client import generate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")


async def claim_job() -> Job | None:
    async with async_session() as session:
        # Find oldest pending job
        result = await session.execute(
            select(Job.id)
            .where(Job.status == JobStatus.pending)
            .order_by(Job.created_at.asc())
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None

        job_id = row[0]

        # Atomically claim it: only succeeds if still pending
        claim = await session.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == JobStatus.pending)
            .values(
                status=JobStatus.processing,
                started_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

        if claim.rowcount == 0:
            return None

        res = await session.execute(select(Job).where(Job.id == job_id))
        return res.scalar_one()


async def complete_job(
    job_id: str,
    result: str,
    input_tokens: int,
    output_tokens: int,
    generation_time_ms: int,
):
    async with async_session() as session:
        res = await session.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one()
        job.status = JobStatus.completed
        job.result = result
        job.input_tokens = input_tokens
        job.output_tokens = output_tokens
        job.generation_time_ms = generation_time_ms
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()


async def fail_job(job_id: str, error: str):
    async with async_session() as session:
        res = await session.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one()
        job.status = JobStatus.failed
        job.error = error
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()


async def process_job(job: Job):
    log.info("Processing job %s (model=%s)", job.id, job.model)
    try:
        result = await generate(
            model=job.model,
            prompt=job.prompt,
            system_prompt=job.system_prompt,
            temperature=job.temperature,
            max_tokens=job.max_tokens,
        )
        await complete_job(
            job.id,
            result=result.response,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            generation_time_ms=result.generation_time_ms,
        )
        log.info(
            "Job %s completed (%d in, %d out tokens, %dms)",
            job.id, result.input_tokens, result.output_tokens, result.generation_time_ms,
        )
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        log.error("Job %s failed: %s", job.id, error_msg)
        await fail_job(job.id, error_msg)


async def main():
    log.info("Worker started, polling every %.1fs", settings.POLL_INTERVAL)
    while True:
        job = await claim_job()
        if job:
            await process_job(job)
        else:
            await asyncio.sleep(settings.POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
