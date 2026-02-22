from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models import Job, JobStatus, Comparison
from backend.app.schemas import ModelLeaderboardEntry

router = APIRouter()


@router.get("/leaderboard", response_model=list[ModelLeaderboardEntry])
async def get_leaderboard(session: AsyncSession = Depends(get_session)):
    # Base stats per model from all jobs
    stats_query = select(
        Job.model,
        func.count().label("total_jobs"),
        func.sum(func.iif(Job.status == JobStatus.completed, 1, 0)).label("completed_jobs"),
        func.sum(func.iif(Job.status == JobStatus.failed, 1, 0)).label("failed_jobs"),
        func.avg(Job.generation_time_ms).label("avg_generation_time_ms"),
        func.coalesce(func.sum(Job.input_tokens), 0).label("total_input_tokens"),
        func.coalesce(func.sum(Job.output_tokens), 0).label("total_output_tokens"),
    ).group_by(Job.model)

    stats_result = await session.execute(stats_query)
    stats_rows = stats_result.all()

    # Compute avg tokens/sec per model from individual completed jobs
    tps_query = select(Job.model, Job.output_tokens, Job.generation_time_ms).where(
        Job.status == JobStatus.completed,
        Job.output_tokens.isnot(None),
        Job.generation_time_ms.isnot(None),
        Job.generation_time_ms > 0,
    )
    tps_result = await session.execute(tps_query)
    tps_rows = tps_result.all()

    model_tps: dict[str, list[float]] = defaultdict(list)
    for model, output_tokens, gen_time_ms in tps_rows:
        model_tps[model].append(output_tokens / (gen_time_ms / 1000))

    avg_tps: dict[str, float] = {}
    for model, values in model_tps.items():
        avg_tps[model] = sum(values) / len(values)

    # Win rate from comparisons
    comparisons_result = await session.execute(
        select(Comparison)
    )
    comparisons = comparisons_result.scalars().all()

    wins: dict[str, int] = defaultdict(int)
    appearances: dict[str, int] = defaultdict(int)

    for comparison in comparisons:
        jobs = comparison.jobs
        # Only consider comparisons where all jobs are terminal
        all_terminal = all(
            j.status in (JobStatus.completed, JobStatus.failed) for j in jobs
        )
        if not all_terminal:
            continue

        # Find completed jobs with valid metrics
        candidates = []
        for j in jobs:
            if (
                j.status == JobStatus.completed
                and j.output_tokens is not None
                and j.generation_time_ms is not None
                and j.generation_time_ms > 0
            ):
                tps = j.output_tokens / (j.generation_time_ms / 1000)
                candidates.append((j.model, tps))

        if len(candidates) < 2:
            continue

        # Track appearances for all completed candidates
        for model, _ in candidates:
            appearances[model] += 1

        # Find winner (highest tokens/sec)
        candidates.sort(key=lambda x: x[1], reverse=True)
        # Check for tie at the top
        if candidates[0][1] != candidates[1][1]:
            wins[candidates[0][0]] += 1

    # Merge into response
    entries = []
    for row in stats_rows:
        model = row.model
        win_count = wins.get(model, 0)
        appearance_count = appearances.get(model, 0)
        win_rate = (win_count / appearance_count) if appearance_count > 0 else None

        entries.append(ModelLeaderboardEntry(
            model=model,
            total_jobs=row.total_jobs,
            completed_jobs=row.completed_jobs,
            failed_jobs=row.failed_jobs,
            avg_tokens_per_second=avg_tps.get(model),
            avg_generation_time_ms=row.avg_generation_time_ms,
            total_input_tokens=row.total_input_tokens,
            total_output_tokens=row.total_output_tokens,
            comparison_wins=win_count,
            comparison_appearances=appearance_count,
            win_rate=win_rate,
        ))

    # Sort by win rate desc, then avg tokens/sec as tiebreaker
    entries.sort(
        key=lambda e: (
            e.win_rate if e.win_rate is not None else -1,
            e.avg_tokens_per_second if e.avg_tokens_per_second is not None else -1,
        ),
        reverse=True,
    )

    return entries
