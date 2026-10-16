# Running AlgoLab locally

These instructions prepare and run the stateless FastAPI backend locally or with Docker.
There is no authentication, database, stored experiment history, live streaming, or
server-side playback/job-control API.

## Python and environment

The package supports Python 3.12 or newer. All 558 tests and strict type checking pass on
Python 3.12.14 and 3.14.8. Python 3.13 has not been separately exercised.

Run these commands from `backend/`. The virtual environment stays in the repository root:

```bash
python3 --version
python3 -m venv ../.venv
source ../.venv/bin/activate
python -m pip install -c requirements.lock -e '.[dev]'
```

Use a Python 3.12+ executable to create the virtual environment if `python3` points to an
older interpreter. The editable development install includes pytest, HTTPX2, Ruff, and mypy.
`requirements.lock` in `backend/` provides exact version constraints for runtime and
development packages.
Constraints restrict versions; they do not install every package named in the file.

For a runtime-only environment, use this install command instead, still from `backend/`:

```bash
python -m pip install -c requirements.lock .
```

No database setup, migration, credential, or external service is needed.

## Start the server

From `backend/`, activate the root virtual environment and start development with automatic
reload:

```bash
source ../.venv/bin/activate
uvicorn main:app --app-dir src --reload
```

For a local session without reload, also from `backend/`:

```bash
source ../.venv/bin/activate
uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000 --workers 1
```

Use **one Uvicorn worker**. Each API process owns its own single CPU worker and admission
queue. Multiple Uvicorn workers would create multiple independent CPU workers and allow
benchmarks to compete, defeating serialization across local API requests. Avoid unrelated
heavy CPU work while making comparisons; AlgoLab cannot isolate timing from other system load.

The local service exposes:

| URL | Purpose |
| --- | --- |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI; send requests interactively |
| [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | ReDoc reference |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | Machine-readable OpenAPI schema |
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Process liveness and version |

Check the server from another terminal:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/api/v1/algorithms
```

The health endpoint remains independent of queued experiments. A healthy API process does
not guarantee an available execution worker; execution failures are reported by experiment
endpoints. For complete requests and response fields, use [API.md](API.md).

## Docker and environment configuration

Run Compose commands from the repository root. It builds the backend from `backend/`, reads
the root `.env`, runs one Uvicorn worker, and publishes the API on host port 8000 by default.

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
curl -sS http://127.0.0.1:8000/health
```

The Compose health check also requests `/health`. View logs with
`docker compose logs -f api`, then stop and remove the container and network with
`docker compose down`.

`.env.example` contains the supported Compose settings. Copy it to `.env` for local changes;
`.env` is ignored by Git and must not contain values that should be committed. Set
`ALGOLAB_PORT` to change the host port, for example `8010`. The app still listens on port
8000 inside the container. `ALGOLAB_CORS_ORIGINS` is an optional comma-separated list of
frontend origins; leave it empty to keep CORS disabled. Recreate the container after changing
settings with `docker compose up -d --force-recreate`.

The image uses Python 3.12, installs the runtime package, and runs as a non-root user. Tests,
docs, local UI files, virtual environments, and `.env` files are excluded from the build
context. The container does not mount the source tree and is intended for repeatable local
API runs; use the Python virtual environment workflow above for automatic reload during
development.

## Execution and cancellation

Sort, benchmark, and suite requests execute in one spawned worker process. This keeps CPU
work out of the API event loop and serializes experiments within the API process. Requests
wait for completed results; the service does not return asynchronous job handles.

At most **four unfinished experiment requests** are admitted: one can execute while up to
three wait. A further request receives HTTP 503 with `error.code="execution_busy"` and
`Retry-After: 1`. Discovery, health, and dataset generation do not consume experiment slots.

Cancelling an HTTP await does not stop an experiment already dispatched to the process pool.
Running work keeps its admission slot until it finishes. Work still cancellable in the
executor's pending queue may be removed. A client disconnect is not a reliable stop control;
retrying may submit a second experiment while the first still runs. There is no hard per-job
execution timeout or result persistence in this version.

Press `Ctrl+C` to stop the development server. Graceful shutdown stops accepting new
connections and waits for active requests, including queued experiments, to finish. During
final cleanup, the executor cancels any remaining cancellable work and waits for dispatched
work. There are no saved experiments to recover after restart. If the worker fails, requests receive
`execution_unavailable`; restart the server after inspecting its logs.

## Resource limits

Every request body is capped at 1,000,000 bytes, including requests without a `Content-Length`
header. Oversized bodies receive HTTP 413. Schema validation then applies numeric, array,
repetition, and suite limits.

The general array limit is 10,000 integer elements. Selection, Bubble, Odd-Even, Cocktail,
Insertion, Binary Insertion, and Shell are capped at 1,000 each. Heap, Quick, and Frequency
advertise a 10,000-element cap; Frequency also requires an inclusive actual value span of at
most 100,000. Traces are limited to 128 elements and 20,000 events per algorithm.

The aggregate budget is 50,000,000 admission units across algorithms and all passes/cases
in a request. This can reject a request that meets every individual size cap. Quick uses
quadratic admission cost to protect against unfavorable inputs; its average theoretical
complexity remains O(n log n). These units are a resource heuristic, not a promised runtime.
Read the [admission formulas](BENCHMARKING.md#suites-and-admission-limits) and
[complete API limits](API.md#input-and-admission-limits) when choosing workloads.

Seeds are unsigned 32-bit integers, from 0 to 4,294,967,295. They reproduce generation/order
choices, not execution timings. Data values are integers from −1,000,000,000 to 1,000,000,000.

## Browser CORS configuration

CORS is disabled by default. To allow a local frontend origin, set
`ALGOLAB_CORS_ORIGINS` before starting the server:

```bash
cd backend
source ../.venv/bin/activate
export ALGOLAB_CORS_ORIGINS='http://localhost:5173,http://127.0.0.1:5173'
uvicorn main:app --app-dir src --reload
```

The setting is a comma-separated list of origins, including scheme and port. Whitespace is
trimmed and empty entries are ignored. Allowed browser methods are GET and POST, the allowed
custom header is `Content-Type`, and credentials are disabled. Restart the server after
changing the environment. CORS controls browser access; it does not add authentication.

## Checks and troubleshooting

Run these from `backend/` in the activated development environment:

```bash
ruff check .
ruff format --check .
mypy
pytest
```

For focused inspection, use `pytest tests/unit/test_algorithms.py` or
`pytest tests/unit/test_application_experiments.py`.

| Symptom | Check |
| --- | --- |
| `uvicorn` missing or an application import fails | Activate `../.venv` from `backend/` and repeat the editable install there |
| Port 8000 is occupied | Stop the other local server or choose `--port 8001`, then update the URLs |
| HTTP 413 | Reduce the JSON body below 1,000,000 bytes |
| HTTP 422 | Read `error.code` and `error.message`; reduce workload or correct request fields |
| HTTP 503 `execution_busy` | Wait before retrying; avoid duplicate requests after cancellation |
| HTTP 503 `execution_unavailable` | Inspect server logs and restart the local server |
| Browser request is blocked by CORS | Match its exact origin in `ALGOLAB_CORS_ORIGINS` and restart |
| Timings vary between runs | Keep the server idle, use repeated samples, and read the benchmark interpretation guide |

For architecture and changes, see [ARCHITECTURE.md](ARCHITECTURE.md) and
[CONTRIBUTING.md](../CONTRIBUTING.md). Local work integrates through `dev`; `main` stays at
its initial baseline until a release is explicitly requested.
