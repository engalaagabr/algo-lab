# AlgoLab

AlgoLab is a FastAPI backend for running, understanding, and comparing sorting algorithms.
It generates reproducible integer datasets, returns operation counts and replayable traces,
and measures repeated runs independently of visualization playback.

The ten implementations are Selection Sort, Bubble Sort, Odd-Even Sort, Cocktail Sort,
Insertion Sort, Binary Insertion Sort, Frequency Sort (ascending Counting Sort), Shell Sort,
Heap Sort, and Quick Sort. Each exposes its variant, theoretical complexity, and input limits.
See the [algorithm guide](docs/ALGORITHMS.md) for details and extension instructions.

This version provides the backend and interactive API documentation. It has no frontend,
authentication, persistent storage, saved experiment history, or live streaming. Clients can
use the returned complete traces to implement their own playback controls.

## Run locally

Requires Python 3.12 or newer. The full 558-test suite passes on Python 3.12.14 and 3.14.8.
Python 3.13 has not been separately exercised.

From the repository root, using Bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e '.[dev]'
uvicorn algolab.main:app --reload
```

Open:

- [Swagger UI](http://127.0.0.1:8000/docs) to send requests interactively.
- [ReDoc](http://127.0.0.1:8000/redoc) to browse the API reference.
- [OpenAPI JSON](http://127.0.0.1:8000/openapi.json) for client generation or tooling.
- [Health](http://127.0.0.1:8000/health) for process liveness.

Run one Uvicorn worker so experiments share one CPU execution worker. The default admission
limit is four unfinished experiment requests, including the running request. Additional
requests receive HTTP 503. See [local operation](docs/RUNNING.md) for configuration and shutdown.

## Try an experiment

```bash
curl -sS http://127.0.0.1:8000/api/v1/sort \
  -H 'Content-Type: application/json' \
  -d '{"values":[5,-2,3,3,0],"algorithm_ids":["insertion_sort","quick_sort"],"trace":true}'
```

Each result contains the same sorted output, its operation metrics, and a complete ordered
event list. Use `/api/v1/benchmarks` for measured performance and `/api/v1/benchmark-suites`
for comparisons across input sizes and distributions. The [API guide](docs/API.md) includes
working requests, response fields, error handling, and trace replay instructions.

## Limits and result interpretation

Requests accept at most 10,000 integers and ten distinct algorithm IDs. Seven algorithms
have a 1,000-element cap; Heap, Quick, and Frequency have a 10,000-element metadata cap.
The aggregate 50,000,000-unit work budget can reject a request below those caps, depending
on selected algorithms, repeats, and suite cases. Quick uses quadratic admission cost even
though its average theoretical time is O(n log n).

Traces allow at most 128 input elements and 20,000 events per algorithm. Request bodies are
capped at 1,000,000 bytes. The API guide lists all numeric, range, seed, and repetition limits.

Timings describe these Python implementations on the current server. The fastest median
belongs to this experiment; it is not a universal ranking. Read
[benchmark methodology](docs/BENCHMARKING.md) before interpreting small timing differences.

## Development checks

With the development environment activated:

```bash
ruff check .
ruff format --check .
mypy
pytest
```

`requirements.lock` supplies exact dependency constraints. Its development-tool pins do not
install those tools unless the requested package extras require them. A runtime-only install
uses `python -m pip install -c requirements.lock .`.

## Project documentation

- [Running and configuration](docs/RUNNING.md)
- [API requests and response contracts](docs/API.md)
- [Architecture and shared contracts](docs/ARCHITECTURE.md)
- [Algorithms and extension guide](docs/ALGORITHMS.md)
- [Benchmarking and interpretation](docs/BENCHMARKING.md)
- [Delivery plan](docs/PLAN.md)
- Phase notes: [foundation](docs/phases/01-foundation.md),
  [algorithms](docs/phases/02-algorithms.md),
  [benchmark engine](docs/phases/03-benchmark-engine.md),
  [FastAPI endpoints](docs/phases/04-fastapi-endpoints.md), and
  [integration and handover](docs/phases/05-integration.md).
- [Contribution workflow](CONTRIBUTING.md)

Development and phase merges are local. GitHub publication is deferred, and `main` remains
at its initial baseline until a release is explicitly requested. No deployment is implied.
