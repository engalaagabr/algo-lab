# Phase 1 — Foundation

Branch: `feat/project-foundation`.

Created the installable Python package, inward dependency boundaries, domain metadata,
registry, errors, shared operation metrics, and trace contracts. Added a five-phase plan,
contribution workflow, and lint/type/test tooling.

Decisions: backend only; stateless first version; integer input; independent timing and
trace passes; local Git workflow while GitHub is deferred. AlgoLab is the working name.

Validation: domain operation and registry tests; lint, formatting, and strict type checking.
No HTTP endpoints or concrete sorting algorithms are part of this phase.
