"""Tests for /api/leaderboard — TPS calc, win rate, sorting, edge cases."""

from datetime import datetime, timezone

from shared.models import Comparison, Job, JobStatus


async def test_leaderboard_empty(client):
    resp = await client.get("/api/leaderboard")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_leaderboard_single_model_no_completions(client, session_factory):
    """A model with only pending jobs should have null avg_tokens_per_second."""
    async with session_factory() as session:
        session.add(Job(model="test:7b", prompt="p", status=JobStatus.pending))
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["model"] == "test:7b"
    assert data[0]["avg_tokens_per_second"] is None
    assert data[0]["total_jobs"] == 1
    assert data[0]["completed_jobs"] == 0


async def test_leaderboard_tps_calculation(client, session_factory):
    """avg_tokens_per_second = avg of (output_tokens / (gen_time_ms / 1000)) per model."""
    async with session_factory() as session:
        # Job 1: 100 tokens in 1000ms = 100 tps
        session.add(Job(
            model="fast:7b", prompt="p1", status=JobStatus.completed,
            output_tokens=100, generation_time_ms=1000, input_tokens=10,
        ))
        # Job 2: 200 tokens in 2000ms = 100 tps
        session.add(Job(
            model="fast:7b", prompt="p2", status=JobStatus.completed,
            output_tokens=200, generation_time_ms=2000, input_tokens=20,
        ))
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["avg_tokens_per_second"] == pytest.approx(100.0)


async def test_leaderboard_tps_excludes_zero_gen_time(client, session_factory):
    """Jobs with generation_time_ms=0 should be excluded from TPS calc."""
    async with session_factory() as session:
        session.add(Job(
            model="test:7b", prompt="p1", status=JobStatus.completed,
            output_tokens=100, generation_time_ms=0, input_tokens=10,
        ))
        session.add(Job(
            model="test:7b", prompt="p2", status=JobStatus.completed,
            output_tokens=50, generation_time_ms=500, input_tokens=10,
        ))
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    # Only the second job contributes: 50 / 0.5 = 100 tps
    assert data[0]["avg_tokens_per_second"] == pytest.approx(100.0)


async def test_leaderboard_tps_excludes_null_tokens(client, session_factory):
    """Jobs with null output_tokens should be excluded from TPS calc."""
    async with session_factory() as session:
        session.add(Job(
            model="test:7b", prompt="p1", status=JobStatus.completed,
            output_tokens=None, generation_time_ms=1000, input_tokens=10,
        ))
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    assert data[0]["avg_tokens_per_second"] is None


async def test_leaderboard_win_rate_basic(client, session_factory):
    """One comparison with a winner should give the winner 100% win rate."""
    async with session_factory() as session:
        comp = Comparison(name="Battle", prompt="Hi")
        session.add(comp)
        await session.flush()

        job_a = Job(model="a:7b", prompt="Hi", status=JobStatus.completed,
                    comparison_id=comp.id, output_tokens=50, generation_time_ms=500, input_tokens=10)
        job_b = Job(model="b:7b", prompt="Hi", status=JobStatus.completed,
                    comparison_id=comp.id, output_tokens=40, generation_time_ms=400, input_tokens=10)
        session.add(job_a)
        session.add(job_b)
        await session.flush()

        comp.winner_job_id = job_a.id
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    a_entry = next(e for e in data if e["model"] == "a:7b")
    b_entry = next(e for e in data if e["model"] == "b:7b")
    assert a_entry["win_rate"] == pytest.approx(1.0)
    assert a_entry["comparison_wins"] == 1
    assert a_entry["comparison_appearances"] == 1
    assert b_entry["win_rate"] == pytest.approx(0.0)
    assert b_entry["comparison_wins"] == 0
    assert b_entry["comparison_appearances"] == 1


async def test_leaderboard_no_winner_set(client, session_factory):
    """Comparisons without a winner still count appearances."""
    async with session_factory() as session:
        comp = Comparison(name="Battle", prompt="Hi")
        session.add(comp)
        await session.flush()

        session.add(Job(model="a:7b", prompt="Hi", status=JobStatus.completed,
                        comparison_id=comp.id, output_tokens=50, generation_time_ms=500, input_tokens=10))
        session.add(Job(model="b:7b", prompt="Hi", status=JobStatus.completed,
                        comparison_id=comp.id, output_tokens=40, generation_time_ms=400, input_tokens=10))
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    a_entry = next(e for e in data if e["model"] == "a:7b")
    assert a_entry["comparison_appearances"] == 1
    assert a_entry["comparison_wins"] == 0
    assert a_entry["win_rate"] == pytest.approx(0.0)


async def test_leaderboard_skips_non_terminal(client, session_factory):
    """Comparisons where jobs are still pending/processing should be skipped for win rate."""
    async with session_factory() as session:
        comp = Comparison(name="Battle", prompt="Hi")
        session.add(comp)
        await session.flush()

        session.add(Job(model="a:7b", prompt="Hi", status=JobStatus.completed,
                        comparison_id=comp.id, output_tokens=50, generation_time_ms=500, input_tokens=10))
        session.add(Job(model="b:7b", prompt="Hi", status=JobStatus.processing,
                        comparison_id=comp.id))
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    a_entry = next(e for e in data if e["model"] == "a:7b")
    assert a_entry["comparison_appearances"] == 0  # skipped because not all terminal


async def test_leaderboard_skips_less_than_two_completed(client, session_factory):
    """Comparisons with <2 completed jobs should be skipped for win rate."""
    async with session_factory() as session:
        comp = Comparison(name="Battle", prompt="Hi")
        session.add(comp)
        await session.flush()

        session.add(Job(model="a:7b", prompt="Hi", status=JobStatus.completed,
                        comparison_id=comp.id, output_tokens=50, generation_time_ms=500, input_tokens=10))
        session.add(Job(model="b:7b", prompt="Hi", status=JobStatus.failed,
                        comparison_id=comp.id))
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    a_entry = next(e for e in data if e["model"] == "a:7b")
    assert a_entry["comparison_appearances"] == 0  # only 1 completed


async def test_leaderboard_sorted_by_win_rate_then_tps(client, session_factory):
    """Models sorted by win_rate desc, then avg_tokens_per_second desc."""
    async with session_factory() as session:
        # Model A: no comparisons, but very fast
        session.add(Job(model="a:7b", prompt="p", status=JobStatus.completed,
                        output_tokens=200, generation_time_ms=1000, input_tokens=10))

        # Model B: comparison winner, slower
        comp = Comparison(name="Battle", prompt="Hi")
        session.add(comp)
        await session.flush()

        job_b = Job(model="b:7b", prompt="Hi", status=JobStatus.completed,
                    comparison_id=comp.id, output_tokens=50, generation_time_ms=1000, input_tokens=10)
        job_c = Job(model="c:7b", prompt="Hi", status=JobStatus.completed,
                    comparison_id=comp.id, output_tokens=40, generation_time_ms=1000, input_tokens=10)
        session.add(job_b)
        session.add(job_c)
        await session.flush()
        comp.winner_job_id = job_b.id
        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    # b:7b should be first (win_rate=1.0), then c:7b (win_rate=0.0), then a:7b (win_rate=None -> -1)
    assert data[0]["model"] == "b:7b"
    assert data[-1]["model"] == "a:7b"


async def test_leaderboard_multiple_comparisons(client, session_factory):
    """Multiple comparisons should accumulate correctly."""
    async with session_factory() as session:
        for i in range(2):
            comp = Comparison(name=f"Battle {i}", prompt="Hi")
            session.add(comp)
            await session.flush()

            job_a = Job(model="a:7b", prompt="Hi", status=JobStatus.completed,
                        comparison_id=comp.id, output_tokens=50, generation_time_ms=500, input_tokens=10)
            job_b = Job(model="b:7b", prompt="Hi", status=JobStatus.completed,
                        comparison_id=comp.id, output_tokens=40, generation_time_ms=400, input_tokens=10)
            session.add(job_a)
            session.add(job_b)
            await session.flush()
            # a:7b wins both
            comp.winner_job_id = job_a.id

        await session.commit()

    resp = await client.get("/api/leaderboard")
    data = resp.json()
    a_entry = next(e for e in data if e["model"] == "a:7b")
    assert a_entry["comparison_wins"] == 2
    assert a_entry["comparison_appearances"] == 2
    assert a_entry["win_rate"] == pytest.approx(1.0)


import pytest  # noqa: E402 — needed for pytest.approx
