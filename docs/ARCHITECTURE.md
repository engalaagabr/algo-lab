# Architecture and extension contracts

AlgoLab is a modular monolith. Dependencies point inward:

```text
presentation (FastAPI) -> application (use cases) -> domain (contracts/rules)
infrastructure (clock/process runner/worker entry points) -> application
algorithms (pure implementations) -> domain
main (API composition root) -> wires HTTP components
infrastructure.worker -> wires worker-local application dependencies
```

The domain has no framework imports. Application services accept a registry and clock;
HTTP, processes, configuration, and JSON conversion are outer details. There is no database
abstraction until persistence is needed.

At the repository root, keep the Python backend in `src/algolab/`, backend tests in `tests/`,
and shared documentation in `docs/`. A future web client belongs in a separate root-level
`frontend/` directory and communicates with the backend over HTTP; it should not import the
Python package. This keeps frontend framework dependencies out of the backend layers.

The FastAPI app factory in `main.py` composes the HTTP process. `infrastructure.executor`
owns process-pool lifecycle and admission, while `infrastructure.worker` contains the
picklable entry points run by the spawned child process and constructs that process's
registry, service, and performance clock. This keeps the execution adapter from importing
the application composition root and avoids creating worker dependencies in the API process.

## Algorithm contract

An `Algorithm` combines immutable metadata with a callable accepting `SortContext`.
The callable sorts `context.values` in place through shared operations. Registry lookup
uses stable snake_case IDs. Algorithms never import HTTP types, read wall clocks, generate
their own input, or mutate shared experiment input.

## Metrics and trace semantics

- `comparisons`: comparisons of input values via `compare`; loop/index checks excluded.
- `swaps`: exchanges of two different indices. One swap produces two `array_writes`.
- `array_writes`: assignments into the working array, even if the assigned value is equal.
- `auxiliary_writes`: logical writes to auxiliary containers, excluding local scalar assignments.
- `writes`: `array_writes + auxiliary_writes`.
- `compare` events carry operand values and any known source indices; an insertion key may
  be held outside the array, so not every comparison operand has an index.
- `swap` events carry the two indices and their values **after** the exchange.
- `write` events carry the target index and newly assigned value.
- Auxiliary writes count toward metrics but do not mutate the displayed main array.
- Event indices are zero-based; sequence numbers are zero-based. Replaying mutation events
  against the original input must reconstruct the sorted output.
- A trace that exceeds its configured limit fails explicitly; successful traces are complete.

Timing uses the same algorithm with counting and tracing disabled. This excludes measurement
instrumentation, but the common operation methods and their disabled-mode branches still
cost time. Results describe these Python implementations on the server, not frontend timing,
hardware-independent constants, or a proof of asymptotic complexity.
