# Phase 6: Docker Compose

## Delivered

- Added a Python 3.12 slim API image with runtime-only dependencies and a non-root runtime
  account.
- Added a Docker health check against `/health` and a Compose service with one Uvicorn worker,
  configurable host port, graceful init process, and restart policy.
- Added `.env.example` for the Compose port and optional CORS origins. The real `.env` and
  environment files are excluded from both Git and the Docker build context.
- Added `.dockerignore` to keep source-control data, local environments, tests, docs, and the
  ignored local playground out of the image build context.
- Documented Python and Compose startup in README and the running guide.

## Validation

- `docker compose config --quiet` accepted the service configuration with the default environment.
- `docker compose build api` built the image successfully.
- Started the container on host port 18080, waited until its Docker health status was
  `healthy`, and confirmed `/health` plus `/api/v1/algorithms` (10 entries) responded.
  The temporary container and network were removed after the smoke check.
- Confirmed `.env` is ignored and `.env.example` remains available to commit.
- No backend API, algorithm, or UI source code was changed.

## Limits

This Compose setup is for repeatable local API runs, not production deployment. It does not
add TLS, authentication, a database, persistent experiment storage, or multiple API workers.
The one-worker setting preserves the backend's per-process experiment serialization.
