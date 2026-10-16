# AlgoLab

AlgoLab is a FastAPI service for sorting algorithm visualization and benchmarking. It runs
selected algorithms on identical integer arrays, returns operation counts and replayable
traces, and measures runtime separately from visualization.

Algorithms: Selection, Bubble, Odd-Even, Cocktail, Insertion, Binary Insertion, Frequency
(Counting), Shell, Heap, and Quick Sort.

## Run with Docker

Requires Docker Engine and the Docker Compose plugin.

```bash
cp .env.example .env
docker compose up --build -d
```

Open [Swagger UI](http://127.0.0.1:8000/docs) (or use the host port set in `.env`). Stop the
service with `docker compose down`.
For configuration or a Python-only setup, see [Running AlgoLab](docs/RUNNING.md).

## API

- `GET /health` — service status.
- `GET /api/v1/algorithms` — available algorithms and complexity metadata.
- `POST /api/v1/datasets` — generate reproducible test data.
- `POST /api/v1/sort` — sort arrays and optionally return operation traces.
- `POST /api/v1/benchmarks` — measure repeated runs on one array.
- `POST /api/v1/benchmark-suites` — compare sizes and input patterns.

Traces support arrays up to 128 values. Other array and algorithm limits apply; see the
[API guide](docs/API.md). Timing results depend on the input and machine and do not identify
a universally fastest algorithm.

## Project guides

- [Architecture and folder layout](docs/ARCHITECTURE.md)
- [Algorithms](docs/ALGORITHMS.md)
- [Benchmarking](docs/BENCHMARKING.md)
- [Contributing](CONTRIBUTING.md)
- [Frontend-to-algorithm flow (Arabic)](docs/FRONTEND-FLOW-AR.md)
