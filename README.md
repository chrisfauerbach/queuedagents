# Queued Agents

A full-stack job queue dashboard for running LLM inference through [Ollama](https://ollama.com) with real-time GPU monitoring. Submit prompts, track job status, and observe GPU utilization, memory, temperature, and token throughput from a single UI.

## Architecture

```
┌────────────┐     ┌──────────┐     ┌──────────┐     ┌────────┐
│  Frontend   │────▶│ Backend  │────▶│  SQLite  │◀────│ Worker │
│ React/Nginx │     │ FastAPI  │     │  (WAL)   │     │ Python │
└────────────┘     └──────────┘     └──────────┘     └───┬────┘
                                         ▲               │
                                         │               ▼
                                   ┌─────┴──────┐  ┌────────┐
                                   │ GPU Monitor │  │ Ollama │
                                   │   pynvml    │  │  LLMs  │
                                   └─────────────┘  └────────┘
```

Five Docker services:

| Service | Role | Port |
|---|---|---|
| **frontend** | React 19 + Vite + Tailwind, served via Nginx | `3001` |
| **backend** | FastAPI REST API | `8001` |
| **worker** | Polls for pending jobs, calls Ollama, writes results | - |
| **gpu-monitor** | Polls NVIDIA GPU metrics via pynvml, writes to DB | - |
| **ollama** | LLM inference server | `11435` |

All Python services share a `shared/` package containing the SQLAlchemy models, database engine, and config.

## Prerequisites

- Docker & Docker Compose
- NVIDIA GPU with drivers installed
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

## Quick Start

```bash
# 1. Clone and configure
git clone git@github.com:chrisfauerbach/queuedagents.git
cd queuedagents
cp .env.example .env

# 2. Launch everything
docker compose up --build -d

# 3. Pull a model into Ollama
docker compose exec ollama ollama pull gemma3:12b

# 4. Open the dashboard
open http://localhost:3001
```

## Configuration

Environment variables (set in `.env`):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/queue.db` | SQLAlchemy async database URL |
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama API base URL |
| `POLL_INTERVAL` | `1.0` | Worker job polling interval (seconds) |
| `GPU_POLL_INTERVAL` | `2.0` | GPU metrics polling interval (seconds) |

## API

All endpoints are prefixed with `/api`.

### Jobs

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/jobs` | Submit a new job |
| `GET` | `/api/jobs` | List jobs (query: `status`, `limit`, `offset`) |
| `GET` | `/api/jobs/:id` | Get a single job |
| `GET` | `/api/stats` | Aggregate job status counts |
| `GET` | `/api/token-usage?hours=24` | Cumulative token usage per model (1-168 hour window) |

### GPU Metrics

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/gpu/metrics?minutes=10` | GPU time-series data (1-60 min window) |

### Comparisons

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/comparisons` | Create a comparison (runs same prompt across N models) |
| `GET` | `/api/comparisons` | List all comparisons with their jobs |
| `GET` | `/api/comparisons/:id` | Get a single comparison with jobs |

### Models

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/models` | List available Ollama models |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Returns `{"status": "ok"}` |

## Job Lifecycle

1. **Submit** a job via the dashboard or API with a model name, prompt, and optional parameters (system prompt, temperature, max tokens).
2. The **worker** picks up the oldest pending job, marks it as `processing`, and sends it to Ollama.
3. On completion, the worker records the result along with **input tokens**, **output tokens**, and **generation time** from the Ollama response.
4. The **dashboard** polls for updates and displays status, results, and token throughput.

## Model Comparison

The Compare feature (`/compare`) lets you run the same prompt against multiple models side-by-side. A comparison creates one job per selected model, all sharing the same prompt and parameters. Results are displayed in a side-by-side grid with per-model status, output, token counts, and generation speed. The detail page auto-refreshes until all jobs complete.

## Token Usage Tracking

The dashboard includes a cumulative token usage chart that tracks input and output tokens consumed per model over time. The chart:

- Shows one line per model, each in a distinct color
- Displays cumulative total tokens on the Y-axis with auto-scaled labels (K/M suffixes)
- Updates every 10 seconds via polling
- Queries the last 24 hours of completed jobs by default

The data is derived from `input_tokens` and `output_tokens` already recorded on each completed job — no additional database tables are required.

## GPU Monitoring

The `gpu-monitor` service reads metrics from NVIDIA GPUs every 2 seconds via `pynvml`:

- GPU utilization %
- Memory used / total (MB)
- Temperature (Celsius)
- Power draw (Watts)

Metrics older than 1 hour are automatically pruned. The dashboard renders a live SVG line chart showing utilization, memory %, and temperature over the selected time window.

## Project Structure

```
queuedagents/
├── backend/             # FastAPI application
│   ├── app/
│   │   ├── main.py      # App entrypoint, CORS, router mounting
│   │   ├── routes/
│   │   │   ├── jobs.py  # Job CRUD + stats endpoints
│   │   │   ├── gpu.py   # GPU metrics endpoint
│   │   │   ├── comparisons.py  # Model comparison endpoints
│   │   │   └── models.py       # Ollama model listing
│   │   └── schemas.py   # Pydantic request/response models
│   ├── alembic/         # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── worker/              # Job processing worker
│   ├── app/
│   │   ├── main.py      # Polling loop, job claim/complete/fail
│   │   └── ollama_client.py  # Ollama HTTP client
│   ├── Dockerfile
│   └── requirements.txt
├── gpu-monitor/         # GPU metrics collector
│   ├── app/
│   │   └── main.py      # pynvml polling loop
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # React SPA
│   ├── src/
│   │   ├── api/client.ts
│   │   ├── components/  # GpuChart, TokenChart, JobList, JobDetail, StatsCards, etc.
│   │   ├── hooks/       # usePolling
│   │   ├── pages/       # DashboardPage, JobDetailPage, ComparePage, ComparisonDetailPage
│   │   └── types/
│   ├── Dockerfile
│   └── nginx.conf
├── shared/              # Shared Python package
│   ├── config.py        # Pydantic settings
│   ├── database.py      # SQLAlchemy async engine + session
│   └── models.py        # Job, Comparison, GpuMetric ORM models
├── docker-compose.yml
└── .env.example
```

## Development

For local frontend development with hot reload:

```bash
cd frontend
npm install
npm run dev
```

This starts Vite on port 3000 with API requests proxied to `localhost:8000`.

## License

MIT
