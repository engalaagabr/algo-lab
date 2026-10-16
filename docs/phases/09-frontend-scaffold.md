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

The client has three pages:

- **Visualize** replays `/sort` traces for up to three algorithms on the same input. Swaps move
  bars, writes change a slot's value, comparisons only highlight, and a held insertion key or
  pivot is shown beside the narration. Each event is explained in one sentence. Playback,
  stepping in both directions, scrubbing, and speed are client-side; the displayed array for
  any step is rebuilt from the input and the trace using periodic checkpoints.
- **Benchmark** measures one generated dataset with `/benchmarks` and charts the median time
  with the sample range, or the exact operation counts. The noise warning is shown when the
  API reports overlapping timing ranges.
- **Suite** runs `/benchmark-suites` over a size and pattern matrix and draws one line chart per
  pattern on a shared scale, so growth rates can be compared. It is limited to three
  algorithms to keep the lines readable.

Pages keep their results while switching tabs. A design selector applies one of five
candidate visual directions to the same screens; the choice is kept in the `theme` URL
parameter so a link opens the same direction. The candidates are under team review and are
expected to be reduced to one.

Validation: `npm run typecheck`, `npm run lint`, `npm test` (35 tests), and `npm run build`
pass. The replay tests use a recorded `/sort` trace for all ten algorithms and check that
replaying every trace reproduces the sorted output, that checkpointed and linear replay agree
at every step, and that event counts match. All three pages were exercised against the
running API in every design at desktop and phone widths. The backend is unchanged.
