# Phase 09: frontend application

Created the web client in `frontend/` with Vite, React, and TypeScript, linted with oxlint and
tested with Vitest. The development server proxies `/api` and `/health` to the backend, so
local development needs no CORS configuration. The proxy target defaults to
`http://127.0.0.1:8000` and can be changed with `ALGOLAB_API_URL`.

API types in `frontend/src/api/schema.ts` are generated from the backend's OpenAPI document
with `openapi-typescript` (`npm run gen:api`). `frontend/src/api/client.ts` wraps
`openapi-fetch` and converts the backend's error envelope into a typed `ApiError`.
`openapi-typescript` declares a TypeScript 5 peer dependency; an npm override lets it use the
project's TypeScript 6.

The client is one page with three sections:

- **Race** replays `/sort` traces for up to ten algorithms on the same input, as small charts
  side by side. Every lane advances one event per step, so the trace with the fewest
  operations finishes first and each lane shows its finishing place. Swaps move bars, writes
  change a slot's value, and comparisons only highlight; each kind has its own trace colour.
  Running operation counts, complexity, stability, and memory use are listed under each chart.
  Playback, stepping in both directions, scrubbing, and speed are client-side; the displayed
  array for any step is rebuilt from the input and the trace using periodic checkpoints.
- **Benchmark** measures one generated dataset with `/benchmarks` and charts the median time
  with the sample range, or the exact operation counts. The noise warning is shown when the
  API reports overlapping timing ranges.
- **Suite** runs `/benchmark-suites` over a size and pattern matrix and draws one line chart per
  pattern on a shared scale, so growth rates can be compared. Three lines are coloured at a
  time and the rest stay grey for context; the legend picks which ones are coloured.

The algorithm selection is shared by all three sections, so adding an algorithm to the race
also adds it to the benchmark and the suite.

The design is Graphite in dark and light modes. The chosen mode is remembered in the browser;
the first visit follows the system preference.

Validation: `npm run typecheck`, `npm run lint`, `npm test` (32 tests), and `npm run build`
pass. The replay tests use a recorded `/sort` trace for all ten algorithms and check that
replaying every trace reproduces the sorted output, that checkpointed and linear replay agree
at every step, and that event counts match. All three pages were exercised against the
running API in both modes at desktop and phone widths. The backend is unchanged.
