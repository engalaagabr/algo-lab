# Contributing to AlgoLab

The repository keeps the applications separate: backend code and Python tools are in
`backend/`, the web client belongs in `frontend/`, and shared documentation stays in `docs/`.
Make changes inside the directory for the application you are contributing to.

We work together in the same GitHub repository. Ask the repository owner to add you as a
collaborator if you do not have access yet. If you cannot push branches to the repository,
use a fork and open your pull request from there.

## Add a feature or fix

Every change gets its own branch, created from the latest `dev`:

```bash
git switch dev
git pull --ff-only origin dev
git switch -c feat/short-task-name
```

Make your changes, then commit and push the branch:

```bash
git add <files-you-changed>
git commit -m "feat: describe the change"
git push -u origin feat/short-task-name
```

On GitHub, open a pull request with:

- **Base:** `dev`
- **Compare:** `feat/short-task-name`

Explain what changed and what checks you ran. A teammate reviews the pull request. Make any
requested updates on the same branch, then push again. Once it is approved, merge it using
**Create a merge commit**.

After the merge, update your local `dev` before starting another task:

```bash
git switch dev
git pull --ff-only origin dev
```

## Keep in mind

- Do not push directly to `dev` or `main`; use a pull request to `dev`.
- `main` is for completed releases. A release is merged from `dev` to `main`.
- Keep commits small and focused. Include useful tests and update documentation when needed.
- Coordinate first if someone else is changing the same files or shared API contracts.
- Do not commit `.env` or the ignored local `local-ui/` folder. `.env.example` is safe to update.
- Domain and application code must not depend on FastAPI or Pydantic.
- Benchmark tests should not assume fixed runtimes or a universally fastest algorithm.

Before opening a backend pull request, run these from `backend/` with the root `.venv` active:

```bash
source ../.venv/bin/activate
ruff check .
ruff format --check .
mypy
pytest
```
