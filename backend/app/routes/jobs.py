from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models import Job, JobStatus
from backend.app.schemas import JobCreate, JobResponse, StatsResponse, TokenUsagePoint

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(payload: JobCreate, session: AsyncSession = Depends(get_session)):
    job = Job(**payload.model_dump())
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    status: JobStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    query = select(Job).order_by(Job.created_at.desc()).limit(limit).offset(offset)
    if status:
        query = query.where(Job.status == status)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/token-usage", response_model=list[TokenUsagePoint])
async def get_token_usage(
    hours: int = Query(24, ge=1, le=168),
    session: AsyncSession = Depends(get_session),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await session.execute(
        select(Job)
        .where(
            Job.status == JobStatus.completed,
            Job.completed_at >= cutoff,
            Job.input_tokens.is_not(None),
            Job.output_tokens.is_not(None),
        )
        .order_by(Job.completed_at.asc())
    )
    jobs = result.scalars().all()

    cumulative: dict[str, dict[str, int]] = defaultdict(
        lambda: {"input": 0, "output": 0, "total": 0, "count": 0}
    )
    points: list[TokenUsagePoint] = []
    for job in jobs:
        c = cumulative[job.model]
        c["input"] += job.input_tokens
        c["output"] += job.output_tokens
        c["total"] += job.input_tokens + job.output_tokens
        c["count"] += 1
        points.append(
            TokenUsagePoint(
                model=job.model,
                timestamp=job.completed_at,
                cumulative_input_tokens=c["input"],
                cumulative_output_tokens=c["output"],
                cumulative_total_tokens=c["total"],
                job_count=c["count"],
            )
        )
    return points


@router.get("/stats", response_model=StatsResponse)
async def get_stats(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Job.status, func.count()).group_by(Job.status)
    )
    counts = {row[0]: row[1] for row in result.all()}
    return StatsResponse(
        pending=counts.get(JobStatus.pending, 0),
        processing=counts.get(JobStatus.processing, 0),
        completed=counts.get(JobStatus.completed, 0),
        failed=counts.get(JobStatus.failed, 0),
        total=sum(counts.values()),
    )
