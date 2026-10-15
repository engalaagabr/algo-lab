# Architecture and extension contracts

AlgoLab is a modular monolith. Dependencies point inward:

```text
presentation (FastAPI) -> application (use cases) -> domain (contracts/rules)
infrastructure (clock/process runner) -> application ports
algorithms (pure implementations) -> domain
bootstrap / main -> wires concrete components together
```

The domain has no framework imports. Application services accept a registry and clock;
HTTP, processes, configuration, and JSON conversion are outer details. There is no database
abstraction until persistence is needed.

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
