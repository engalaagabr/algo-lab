# Phase 7: Worker composition boundary

## Delivered

- Moved the picklable process-pool entry points to `infrastructure/worker.py`.
- The worker module constructs its own registry, application service, and performance clock
  inside the spawned child process.
- Kept `infrastructure/executor.py` focused on queue admission, process-pool lifecycle, and
  async result handling.
- Removed the old `bootstrap.py` module. It was only used by the worker to construct its
  service, which made the infrastructure adapter depend on the composition root.
- Documented the API-process and child-worker composition boundaries.

## Behavior and validation

The HTTP routes, request and response models, API paths, worker count, admission limits, and
algorithm implementations are unchanged. The process task callables remain top-level module
functions so `ProcessPoolExecutor` can import them under spawn.

Static import-reference review confirmed `bootstrap.py` had no other project callers. Automated
tests were not run for this documentation and composition-only refactor.
