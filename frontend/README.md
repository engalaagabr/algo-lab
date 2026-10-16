# AlgoLab frontend

The web client for AlgoLab: Vite, React, and TypeScript. It talks to the backend only over
HTTP and never imports backend code.

## Page

The client is a single page with three sections:

- **Race**: replays sort traces for up to ten algorithms side by side on the same array. Every
  lane advances one operation per step, so the algorithm with the fewest operations finishes
  first. Compares, swaps, and writes each have their own trace colour, and the operation counts
  and complexity are listed under each chart. Space plays or pauses, the arrow keys step, R
  resets, and End jumps to the last step.
- **Benchmark**: times algorithms on one generated dataset and compares the median time or the
  exact operation counts.
- **Suite**: compares how work grows across input sizes and patterns.

The design is Graphite, in dark and light modes; the top bar switches between them.

## Run locally

Start the API first (see [Running AlgoLab](../docs/RUNNING.md)), then from `frontend/`:

```bash
npm install
npm run dev
```

Open <http://localhost:5173>. The dev server proxies `/api` and `/health` to
`http://127.0.0.1:8000`, so the browser makes same-origin requests and the API does not need
CORS during development. To use another API address:

```bash
ALGOLAB_API_URL=http://127.0.0.1:9000 npm run dev
```

## Scripts

| Script | Purpose |
| --- | --- |
| `npm run dev` | Development server with the API proxy |
| `npm run build` | Type-check and build static files into `dist/` |
| `npm run typecheck` | TypeScript check only |
| `npm run lint` | Lint with oxlint |
| `npm test` | Run unit tests with Vitest |
| `npm run gen:api` | Regenerate `src/api/schema.ts` from the running API's OpenAPI document |

## Source layout

| Path | Contents |
| --- | --- |
| `src/api/` | Generated schema types and the typed client |
| `src/replay/` | Trace replay engine, with tests |
| `src/visualizer/` | Race section: lanes, playback, and transport controls |
| `src/benchmark/`, `src/suite/` | Benchmark and suite sections |
| `src/charts/` | Bar and line charts |
| `src/shared/` | Shared controls, formatting, styles, and colour mode |

## API types

`src/api/schema.ts` is generated from `/openapi.json`; do not edit it by hand. Regenerate it
whenever the backend's request or response schemas change, and commit it with that change so
type errors show where the frontend must adapt. `ALGOLAB_API_URL` also applies to
`gen:api`.

`src/api/client.ts` exports a typed client (`api`), short type aliases such as `SortEvent`
and `AlgorithmMetadata`, and `request()`, which returns the response data or throws an
`ApiError` carrying the HTTP status and the API's `error.code`. Network failures use the
`network_error` code.

A build served from a different origin than the API sets `VITE_API_BASE_URL` at build time,
and the API's `ALGOLAB_CORS_ORIGINS` must then include that origin.
