# Contributing

AlgoLab uses `dev` as the shared integration branch. Keep `main` for complete releases.
The project team collaborates in the same GitHub repository: repository owners add team
members as collaborators with write access. Use a fork and a pull request from the fork only
when a contributor does not have write access.

## Branch workflow

Create each feature, fix, or documentation branch from the latest `dev`. Keep branches
focused and short-lived. Make small, coherent commits as work progresses, and add or update
tests and documentation with the change.

```bash
git fetch origin
git switch dev
git pull --ff-only origin dev
git switch -c feat/my-task

# Implement the change, document its phase, and run the required checks.
git add <specific-paths>
git commit -m "feat: describe the change"
git push -u origin feat/my-task
```

Open a pull request on GitHub from `feat/my-task` to the repository's `dev` branch. Describe
the behavior that changed, the checks you ran, and any limits or follow-up work. A teammate
reviews the pull request; address review comments with additional commits on the same branch.
After approval and passing checks, merge the pull request into `dev` using GitHub's **Create
a merge commit** option. This preserves the feature branch history and is the GitHub
equivalent of `git merge --no-ff`.

Once the pull request is merged, update local `dev` before starting the next task:

```bash
git switch dev
git pull --ff-only origin dev
git branch -d feat/my-task
```

Do not merge daily work directly into `main`. When `dev` contains a complete release, promote
it to `main` through a reviewed release pull request. If an urgent fix must go directly to
`main`, merge that fix back into `dev` too.

For contributors with write access who need to merge locally instead of through a pull
request, update `dev`, merge with `--no-ff`, and push it:

```bash
git switch dev
git pull --ff-only origin dev
git merge --no-ff feat/my-task
git push origin dev
```

Prefer the pull request workflow so review, checks, and the merge record are visible together.

## Parallel work

Before starting, agree on ownership when two tasks need to change the same files or shared
contracts. Each contributor should work on their own branch; avoid sharing a checked-out
feature branch. If a task depends on another unmerged change, coordinate with its author or
wait for its pull request to reach `dev` before building on it.

## Project boundaries

- Algorithm authors own the implementation, complexity metadata, and correctness tests.
- API request and response models belong at the presentation boundary.
- Domain and application modules must not import FastAPI or Pydantic.
- Never assert machine-specific timing thresholds or claim an algorithm is universally fastest.
- The local playground under `local-ui/` is ignored by Git; do not force-add or include it in
  commits or pull requests unless the project owner changes that instruction.

## Required checks

Run these checks before requesting review:

```bash
ruff check .
ruff format --check .
mypy
pytest
```

Record the phase's changes, validation, and limitations in the relevant project documentation.
