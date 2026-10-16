# Phase 08: separate backend and frontend applications

Moved the FastAPI application, Python packaging configuration, dependency constraints,
container build files, and tests under `backend/`. Added a tracked `frontend/` home for the
future web application. Shared documentation and Docker Compose remain at the repository
root, and Compose now builds from the backend directory only.

Updated the architecture, running, contributing, and algorithm guides to match the new
paths. The API behavior and Python package structure inside `backend/src/algolab/` are
unchanged.
