from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models import Job, JobStatus
from backend.app.schemas import JobCreate, JobResponse, StatsResponse

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
