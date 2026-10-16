# AlgoLab web client

The React and TypeScript single-page app presents the current sorting experiments and talks
to the FastAPI backend over HTTP. It does not import backend code.

## Current site functionality

- **Race:** replay traces for up to ten selected sorting algorithms on the same array, with
  playback controls, speed selection, and highlighted comparisons, swaps, writes, and sorted
  values.
- **Benchmark:** compare selected algorithms on one dataset using repeated timings and
  operation counts.
- **Suite:** compare algorithm metrics across input sizes and data distributions.
- **Shared selection:** adding or removing an algorithm in any of the three sections updates
  the other sections.
- Dark and light themes, deterministic dataset seeds, and keyboard playback controls.

Sorting is the only active category. Searching, Graphs, Dynamic Programming, and Backtracking
are planned; their tabs are currently disabled placeholders.

## Run through Docker Compose

From the repository root:

```bash
cp .env.example .env
docker compose up --build -d
```

Open <http://127.0.0.1:8081>. Nginx serves the production build and proxies `/api` and
`/health` to the API service, keeping browser requests same-origin. See the root
[README](../README.md) and [running guide](../docs/RUNNING.md) for more details.

## Run the development server

Start the backend first (see [Running AlgoLab](../docs/RUNNING.md)), then run from
`frontend/`:

```bash
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` and `/health` to
`http://127.0.0.1:8000`. To use another local API:

```bash
ALGOLAB_API_URL=http://127.0.0.1:9000 npm run dev
```

## Checks and scripts

| Script | Purpose |
| --- | --- |
| `npm run dev` | Vite development server with API proxy |
| `npm run build` | Type-check and build static files into `dist/` |
| `npm run typecheck` | TypeScript check only |
| `npm run lint` | Lint with oxlint |
| `npm test` | Run unit tests with Vitest |
| `npm run gen:api` | Regenerate API schema types from `/openapi.json` |

`src/api/schema.ts` is generated; do not edit it by hand. Regenerate and commit it whenever
the backend API schema changes.
