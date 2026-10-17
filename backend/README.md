# AlgoLab API

The backend is the FastAPI application that provides algorithm discovery, dataset
generation, sort traces, repeated benchmarks, and benchmark suites. Sorting implementations
are registered in Python and run behind the application layer; the API also reports
complexity metadata and operation counts.

The current algorithm set is Selection, Bubble, Odd-Even, Cocktail, Insertion, Binary
Insertion, Frequency (Counting), Shell, Heap, Quick, and Merge Sort. Planned search, graph,
dynamic-programming, and backtracking features are not implemented in the API yet.

## Run and develop

For the full site, use Docker Compose from the repository root. For backend-only local
development, follow [Running AlgoLab](../docs/RUNNING.md). The HTTP contracts and limits
are in the [API guide](../docs/API.md), and internal module responsibilities are described
in [Architecture](../docs/ARCHITECTURE.md).

Backend checks from this directory, with the repository-root virtual environment active:

```bash
source ../.venv/bin/activate
ruff check .
ruff format --check .
mypy
pytest
```

The API is stateless: experiments and generated datasets are not persisted. A single
execution worker serializes CPU-heavy experiment requests within each API process.
