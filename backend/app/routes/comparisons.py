from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models import Comparison, Job, JobStatus
from backend.app.schemas import ComparisonCreate, ComparisonResponse, SetWinnerRequest

router = APIRouter()


@router.post("/comparisons", response_model=ComparisonResponse, status_code=201)
async def create_comparison(
    payload: ComparisonCreate, session: AsyncSession = Depends(get_session)
):
    comparison = Comparison(
        name=payload.name,
        prompt=payload.prompt,
        system_prompt=payload.system_prompt,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    session.add(comparison)
    await session.flush()

    for model_name in payload.models:
        job = Job(
            model=model_name,
            prompt=payload.prompt,
            system_prompt=payload.system_prompt,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            comparison_id=comparison.id,
        )
        session.add(job)

    await session.commit()
    await session.refresh(comparison)
    return comparison


@router.get("/comparisons", response_model=list[ComparisonResponse])
async def list_comparisons(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Comparison).order_by(Comparison.created_at.desc())
    )
    return result.scalars().all()


@router.get("/comparisons/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    comparison_id: str, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Comparison).where(Comparison.id == comparison_id)
    )
    comparison = result.scalar_one_or_none()
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return comparison


@router.put("/comparisons/{comparison_id}/winner", response_model=ComparisonResponse)
async def set_winner(
    comparison_id: str,
    payload: SetWinnerRequest,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Comparison).where(Comparison.id == comparison_id)
    )
    comparison = result.scalar_one_or_none()
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Validate that the job belongs to this comparison and is completed
    job_result = await session.execute(
        select(Job).where(
            Job.id == payload.winner_job_id,
            Job.comparison_id == comparison_id,
        )
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found in this comparison")
    if job.status != JobStatus.completed:
        raise HTTPException(status_code=400, detail="Job is not completed")

    comparison.winner_job_id = payload.winner_job_id
    await session.commit()
    await session.refresh(comparison)
    return comparison


@router.delete("/comparisons/{comparison_id}/winner", response_model=ComparisonResponse)
async def clear_winner(
    comparison_id: str, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Comparison).where(Comparison.id == comparison_id)
    )
    comparison = result.scalar_one_or_none()
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    comparison.winner_job_id = None
    await session.commit()
    await session.refresh(comparison)
    return comparison
