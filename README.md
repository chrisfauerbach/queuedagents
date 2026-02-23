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
| `GET` | `/api/models/catalog` | Curated model catalog with installed status |
| `POST` | `/api/models/pull` | Pull/download a model (streams NDJSON progress) |
| `POST` | `/api/models/show` | Get detailed model info (license, family, quantization) |
| `DELETE` | `/api/models` | Delete a local model |

### Prompts

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/prompts` | Save a reusable prompt |
| `GET` | `/api/prompts` | List all saved prompts |
| `GET` | `/api/prompts/:id` | Get a single prompt |
| `PUT` | `/api/prompts/:id` | Update a prompt |
| `DELETE` | `/api/prompts/:id` | Delete a prompt |

### Leaderboard

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/leaderboard` | Model performance leaderboard with win rates |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Returns `{"status": "ok"}` |

## Job Lifecycle

1. **Submit** a job via the dashboard or API with a model name, prompt, and optional parameters (system prompt, temperature, max tokens).
2. The **worker** picks up the oldest pending job, marks it as `processing`, and sends it to Ollama.
3. On completion, the worker records the result along with **input tokens**, **output tokens**, and **generation time** from the Ollama response.
4. The **dashboard** polls for updates and displays status, results, and token throughput.

## Model Management

The Models page (`/models`) provides a full model management interface:

- **Installed models table** — Shows name, size, family, parameters, and quantization for all local models. Two-click delete confirmation.
- **Curated catalog** — Browse ~15 model families across 6 categories (General Purpose, Code, Reasoning, Chat/Instruct, Small/Fast, Multilingual). Click a variant chip to pull it.
- **Real-time download progress** — Pull streams NDJSON from Ollama with animated progress bars.
- **Custom pull** — Text input for pulling any model by name (e.g. `llama3.1:8b`).

## Model Comparison

The Compare feature (`/compare`) lets you run the same prompt against multiple models side-by-side. A comparison creates one job per selected model, all sharing the same prompt and parameters. Results are displayed in a side-by-side grid with per-model status, output, token counts, and generation speed. The detail page auto-refreshes until all jobs complete.

## Prompt Library

The Prompts page (`/prompts`) lets you save reusable prompts with parameters (system prompt, temperature, max tokens). Saved prompts can be edited, deleted, run directly as a comparison against selected models, or sent to the Compare page pre-filled.

## Model Leaderboard

The Leaderboard page (`/leaderboard`) ranks models by performance metrics including average tokens per second, generation time, total token usage, and comparison win rate.

## Token Usage Tracking

The dashboard includes a cumulative token usage chart that tracks input and output tokens consumed per model over time. The chart:

- Shows one line per model, each in a distinct color (16-color palette)
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
│   │   │   ├── models.py       # Model listing, catalog, pull, show, delete
│   │   │   ├── prompts.py      # Prompt CRUD endpoints
│   │   │   └── leaderboard.py  # Model leaderboard endpoint
│   │   ├── model_catalog.py    # Curated model catalog data
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
│   │   ├── components/  # GpuChart, TokenChart, JobList, JobDetail, StatsCards, Layout, etc.
│   │   ├── hooks/       # usePolling
│   │   ├── pages/       # Dashboard, JobDetail, Prompts, Compare, ComparisonDetail, Leaderboard, Models
│   │   └── types/
│   ├── Dockerfile
│   └── nginx.conf
├── shared/              # Shared Python package
│   ├── config.py        # Pydantic settings
│   ├── database.py      # SQLAlchemy async engine + session
│   └── models.py        # Job, Comparison, GpuMetric, Prompt ORM models
├── tests/               # 136 pytest tests (97% coverage)
│   ├── conftest.py      # In-memory DB, session, and ASGI client fixtures
│   └── test_*.py        # 16 test modules
├── requirements-test.txt
├── pytest.ini
├── docker-compose.yml
└── .env.example
```

## Testing

The backend has a comprehensive test suite covering all Python services: backend (FastAPI routes), worker (job processing), gpu-monitor (metrics collection), and shared (models, config, database).

### Running Tests

```bash
# One-time setup
ln -sf gpu-monitor gpu_monitor
pip install -r requirements-test.txt

# Run all 136 tests with coverage
pytest --cov --cov-report=term-missing -v

# Run a single test file
pytest tests/test_routes_jobs.py -v
```

### What Gets Mocked

The test suite runs entirely offline — no Docker, no GPU, no Ollama needed. Three external systems are mocked out:

| System | Mock Strategy | Why |
|---|---|---|
| **SQLite database** | Replaced with an in-memory SQLite engine (`sqlite+aiosqlite://`). Each test gets a fresh database via function-scoped fixtures — tables are created before the test and dropped after. | Eliminates filesystem I/O, prevents test pollution, runs in milliseconds. |
| **Ollama HTTP API** | Intercepted at the `httpx` transport layer using [respx](https://github.com/lundberg/respx). Routes that call Ollama (`/api/models`, `/api/models/catalog`, `/api/models/show`, `/api/models/pull`, `DELETE /api/models`) and the worker's `generate()` function all get deterministic fake responses. | Ollama requires a running server with downloaded models. Mocking lets us test every code path — success, HTTP errors, missing fields, timeouts — without a live inference server. |
| **NVIDIA GPU driver (pynvml)** | The entire `pynvml` module is replaced via `unittest.mock.patch` with a `MagicMock` that returns `SimpleNamespace` objects mimicking real GPU handles, utilization rates, memory info, temperature, and power readings. | The gpu-monitor service calls `pynvml.nvmlDeviceGetHandleByIndex()` and related C library bindings that require an NVIDIA GPU. Mocking lets us verify unit conversions (milliwatts → watts, bytes → megabytes), multi-GPU iteration, metric pruning, and error handling. |

### Test Structure

```
tests/
├── conftest.py                  # Shared fixtures (engine, session, FastAPI client)
├── test_shared_config.py        # Settings defaults and env overrides
├── test_shared_models.py        # ORM defaults, relationships, enums
├── test_shared_database.py      # Engine, Base metadata, get_session
├── test_backend_main.py         # Health endpoint, CORS, router registration
├── test_backend_schemas.py      # Pydantic validation on all request schemas
├── test_backend_seed.py         # Prompt seeding logic and idempotency
├── test_model_catalog.py        # Catalog structure and data integrity
├── test_routes_jobs.py          # Job CRUD, token-usage cumulative logic, stats
├── test_routes_comparisons.py   # Comparison CRUD, set/clear winner validation
├── test_routes_gpu.py           # GPU metrics query with time filtering
├── test_routes_models.py        # Ollama proxy endpoints (respx mocks)
├── test_routes_leaderboard.py   # TPS calculation, win rate, sorting
├── test_routes_prompts.py       # Prompt CRUD with partial updates
├── test_worker_main.py          # Job claim/complete/fail lifecycle, main loop
├── test_worker_ollama.py        # generate() request/response handling
└── test_gpu_monitor.py          # Record/prune metrics, main loop resilience
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
