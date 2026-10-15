# Contributing

## Branches

- `dev`: shared, runnable integration branch. Start each task from the latest `dev`.
- `feat/<task>`, `fix/<task>`, `docs/<task>`: short-lived task branches.
- `main`: stable releases; never a daily development target.

Commit small coherent changes during each task. Include tests and a phase note explaining
what changed, validation, and limitations. Merge completed task branches into `dev` after
checks pass. For GitHub collaboration, use a PR reviewed by another contributor. GitHub is
currently deferred by the project owner; phase merges are local and recorded as merge commits.

```bash
git switch dev
git switch -c feat/my-task
# Implement, document, and run the checks below.
git add <specific-paths>
git commit -m "feat: describe the completed change"
git switch dev
git merge --no-ff feat/my-task
```

Keep `main` and `dev` history intact: use a merge commit for release promotions. If a fix
lands directly through a hotfix PR into `main`, merge it back into `dev` as well.

## Required checks

```bash
ruff check .
ruff format --check .
mypy
pytest
```

Agree on shared contracts before changing them. Algorithm authors own their implementation,
complexity metadata, and correctness tests. API models belong to the presentation boundary;
the domain and application must not import FastAPI or Pydantic. Never assert machine-specific
timing thresholds or a universally fastest algorithm in tests.
