# CLAUDE.md

## Project Overview

Queued Agents is a Dockerized job queue dashboard for LLM inference via Ollama with GPU monitoring. Five services: frontend (React/Nginx), backend (FastAPI), worker (job processor), gpu-monitor (pynvml metrics), and ollama.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), aiosqlite, Pydantic Settings
- **Worker**: Python 3.12, httpx (Ollama client), SQLAlchemy
- **GPU Monitor**: Python 3.12, pynvml (nvidia-ml-py), SQLAlchemy
- **Frontend**: React 19, TypeScript, Vite 6, Tailwind CSS 3, React Router 7
- **Database**: SQLite with WAL mode, shared across services via volume mount at `./data/`
- **Infra**: Docker Compose, NVIDIA Container Toolkit for GPU access

## Project Layout

```
shared/           # Shared Python package — models, database engine, config
backend/app/      # FastAPI app — routes in routes/, schemas in schemas.py
worker/app/       # Job processing loop + Ollama HTTP client
gpu-monitor/app/  # GPU metrics polling loop
frontend/src/     # React SPA — components/, pages/, hooks/, api/, types/
```

All Python services import from `shared/` (models, database, config). `PYTHONPATH=/app` is set in each Dockerfile. Each service has its own `Dockerfile` and `requirements.txt`.

## Key Patterns

- **Database access**: All services use `shared.database.async_session` for SQLAlchemy async sessions. The backend uses FastAPI dependency injection via `get_session()`.
- **ORM models**: Defined in `shared/models.py` using SQLAlchemy 2.0 `Mapped` style. Tables are auto-created on startup via `Base.metadata.create_all`.
- **API schemas**: Pydantic models in `backend/app/schemas.py` with `model_config = {"from_attributes": True}` for ORM compatibility.
- **Frontend polling**: `usePolling(fetcher, intervalMs)` hook handles all data fetching with auto-refresh. API client functions are in `frontend/src/api/client.ts`.
- **Frontend routing**: React Router with seven pages — `DashboardPage` (/), `JobDetailPage` (/jobs/:id), `PromptsPage` (/prompts), `ComparePage` (/compare), `ComparisonDetailPage` (/compare/:id), `LeaderboardPage` (/leaderboard), and `ModelsPage` (/models).
- **No chart libraries**: GPU and token usage charts use raw inline SVG (`GpuChart.tsx`, `TokenChart.tsx`).
- **Streaming**: The model pull endpoint streams NDJSON progress. Nginx has `proxy_buffering off` for `/api/models/pull`. The frontend reads the stream via `fetch()` + `getReader()`.
- **Model catalog**: Curated list in `backend/app/model_catalog.py`, cross-referenced with locally installed models via Ollama's `/api/tags`.
- **Config**: `shared/config.py` uses Pydantic Settings, reads from `.env` file. Key vars: `DATABASE_URL`, `OLLAMA_HOST`, `POLL_INTERVAL`, `GPU_POLL_INTERVAL`.

## Build & Run

```bash
docker compose up --build -d      # Build and start all services
docker compose logs <service>     # View logs for a service
docker compose ps                 # Check service status
```

- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- Ollama: http://localhost:11435

## Database

SQLite at `./data/queue.db`. Four tables:
- `jobs` — Job queue with status tracking, token counts, generation time. Has optional `comparison_id` FK to `comparisons`.
- `comparisons` — Model comparison groups. Each comparison spawns one job per model with shared prompt/params.
- `gpu_metrics` — Time-series GPU metrics, auto-pruned to 1 hour
- `prompts` — Saved reusable prompts with parameters

Schema changes require deleting the DB file (`rm data/queue.db`) and restarting, since `create_all` only adds missing tables. Alembic is configured but migrations are not currently used for new columns.

## Testing Notes

- Submit a test job: `curl -X POST http://localhost:8001/api/jobs -H 'Content-Type: application/json' -d '{"model":"gemma3:12b","prompt":"Hello"}'`
- Create a comparison: `curl -X POST http://localhost:8001/api/comparisons -H 'Content-Type: application/json' -d '{"name":"Test","prompt":"Hello","models":["mistral:7b","qwen2.5:7b"]}'`
- List comparisons: `curl http://localhost:8001/api/comparisons`
- Check GPU metrics: `curl http://localhost:8001/api/gpu/metrics?minutes=1`
- Model catalog: `curl http://localhost:8001/api/models/catalog`
- Pull a model (streaming): `curl -N -X POST http://localhost:8001/api/models/pull -H 'Content-Type: application/json' -d '{"name":"tinyllama:1.1b"}'`
- Delete a model: `curl -X DELETE http://localhost:8001/api/models -H 'Content-Type: application/json' -d '{"name":"tinyllama:1.1b"}'`
- Health check: `curl http://localhost:8001/api/health`

## Style Conventions

- Python: snake_case, type hints, async/await throughout
- TypeScript: named exports for hooks/functions, default exports for components
- Commits: imperative mood, concise summary line, body for details
