from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models import Comparison, Job
from backend.app.schemas import ComparisonCreate, ComparisonResponse

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
