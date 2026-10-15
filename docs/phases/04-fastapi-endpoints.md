# Phase 4 — FastAPI endpoints

Branch: `feat/fastapi-endpoints`.

## Delivered

- `/health`, algorithm catalog/detail, dataset generation, sorting with optional complete
  traces, repeated benchmarks, and size/distribution benchmark suites.
- Strict request schemas, typed OpenAPI responses, consistent experiment errors,
  request-byte limits (including chunked bodies), and optional configured CORS origins.
- An application execution port with a single spawned CPU worker. At most four running
  plus queued requests are admitted; full capacity returns 503 with Retry-After.
- Application lifespan owns worker shutdown. Cancelling a waiting request does not release
  the slot of work that is still running.
- Output validation failures become sanitized 500 responses. Unknown algorithm IDs return
  404; invalid data and experiment limits return 422; bodies above 1 MB return 413.

## Review correction

A concrete even-then-odd input triggers quadratic work in the median-of-three Quick Sort.
Its admission class now reserves quadratic work, independently of its O(n log n) average
complexity. A regression test proves oversized repeated experiments are rejected before
the first algorithm call. This deliberately limits some large Quick experiments.

## Validation

555 tests passed in the combined suite, including 91 HTTP contract tests, actual spawned
process execution of every experiment endpoint, cancellation/capacity accounting, chunked
request limits, and strict request validation. Ruff lint/format and mypy strict passed.
The installed Starlette test client emits one compatibility deprecation warning for httpx;
the HTTP and process tests pass.

The backend returns complete traces for future client playback. Server-side pause/resume,
streaming jobs, persistent experiment history, and frontend rendering are outside this phase.
