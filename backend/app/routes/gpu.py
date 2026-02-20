from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models import GpuMetric
from backend.app.schemas import GpuMetricResponse

router = APIRouter()


@router.get("/gpu/metrics", response_model=list[GpuMetricResponse])
async def get_gpu_metrics(
    minutes: int = Query(10, ge=1, le=60),
    session: AsyncSession = Depends(get_session),
):
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    result = await session.execute(
        select(GpuMetric)
        .where(GpuMetric.recorded_at >= since)
        .order_by(GpuMetric.recorded_at.asc())
    )
    return result.scalars().all()
