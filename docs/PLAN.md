# Delivery plan

Scope: FastAPI backend, modular clean architecture, ten agreed sorting algorithms, and
repeatable local Docker Compose execution. Each phase has its own feature branch, incremental
commits, checks, phase documentation, and merge into `dev`. `main` is reserved for releases.

| Phase | Branch | Deliverable |
| --- | --- | --- |
| 1 | `feat/project-foundation` | Package, domain contracts, architecture, quality tooling |
| 2 | `feat/sorting-algorithms` | Ten algorithms, shared metrics, replayable operation traces |
| 3 | `feat/benchmark-engine` | Reproducible datasets, sorting, repeated benchmarks, suites |
| 4 | `feat/fastapi-endpoints` | Versioned API, validation, isolated CPU execution, OpenAPI |
| 5 | `feat/integration-docs` | Integration verification, usage examples, deployment docs |
| 6 | `feat/docker-compose` | Non-root API image, Compose service, health check, environment template |
| 7 | `refactor/worker-composition` | Isolate process worker entry points from API composition |
| 8 | `refactor/mono-repo-layout` | Separate backend and frontend applications at the repository root |
| 9 | `feat/frontend-scaffold` | Web client: trace visualizer, benchmark and suite pages, generated API types |

Phases 1–6 are complete. Phase 7 clarifies the process worker boundary, and phase 8 organizes
the applications into sibling directories. See the numbered reports under [phases](phases/)
for changes and validation. The initial backend handover is documented in
[phase 5](phases/05-integration.md); the latest architecture cleanup is in
[phase 7](phases/07-worker-composition.md); the latest directory layout is in
[phase 8](phases/08-repository-layout.md); the first web
client is in [phase 9](phases/09-frontend-scaffold.md).

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
