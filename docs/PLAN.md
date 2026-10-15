# Delivery plan

Scope: backend only, FastAPI, modular clean architecture, ten agreed sorting algorithms.
Each phase has its own feature branch, incremental commits, checks, phase documentation,
and a local merge into `dev`. GitHub publication is deferred. `main` stays at its initial
baseline until a release is explicitly requested.

| Phase | Branch | Deliverable |
| --- | --- | --- |
| 1 | `feat/project-foundation` | Package, domain contracts, architecture, quality tooling |
| 2 | `feat/sorting-algorithms` | Ten algorithms, shared metrics, replayable operation traces |
| 3 | `feat/benchmark-engine` | Reproducible datasets, sorting, repeated benchmarks, suites |
| 4 | `feat/fastapi-endpoints` | Versioned API, validation, isolated CPU execution, OpenAPI |
| 5 | `feat/integration-docs` | Integration verification, usage examples, deployment docs |

All five phases are complete and integrated into `dev`. See the corresponding numbered
reports under [phases](phases/) for changes and validation. The completed handover is
documented in [phase 5](phases/05-integration.md).

## Initial implementation choices

- Integers, including negative and duplicate values; ascending ordering.
- Frequency Sort means counting frequencies and reconstructing values in ascending order.
- Random, sorted, reversed, nearly sorted, and few-unique distributions; reproducible seeds.
- Every algorithm receives its own copy of identical input; sorted output is verified
  against Python's `sorted`, including multiplicity.
- Timing, operation counting, and trace capture are separate runs. Timing excludes input
  generation/copying, validation, serialization, and playback. Algorithm control-flow and
  operation helper overhead remain part of the measured implementation.
- Stateless HTTP responses. No database, accounts, stored experiment history, or frontend.
- Trace responses support future client-side start/pause/resume/speed/reset playback.
  They are completed traces, not a live streaming or server-side job-control protocol.
- Bounded inputs, repeats, trace sizes, suite sizes, and execution admission protect the API.

These choices are documented defaults for the first backend, not constraints on future features.
