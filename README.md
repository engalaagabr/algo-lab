# AlgoLab

FastAPI backend for learning, running, and comparing sorting algorithms. Visualization data
and performance measurements are separate so playback speed never changes benchmark results.

The implementation is being delivered through documented feature branches into `dev`.
See [the delivery plan](docs/PLAN.md), [architecture](docs/ARCHITECTURE.md), and
[contribution workflow](CONTRIBUTING.md).

## Local development

Requires Python 3.12 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy
```
