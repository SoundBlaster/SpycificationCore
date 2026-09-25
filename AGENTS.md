# Development rules

## Project scope

- This repository implements the Python SpecificationCore library. Support Python 3.10 and newer.
- Keep runtime dependencies at zero. Add development tools to the `dev` optional dependency group in `pyproject.toml`.
- Keep public API compatibility decisions in `docs/compatibility.md`; export public names from `src/specification_core/__init__.py`.

## Design and implementation

- Prefer small, typed objects with constructor-established invariants and no public mutation.
- Mark concrete built-in implementations `@final` when callers are not expected to subclass them. Keep abstract extension points open so users can define their own specifications and decisions.
- Follow the SpecificationCore model: specifications compute deterministic results and optional traces; calling code owns side effects such as publishing or network access.
- Preserve explicit `MatchResult` no-match semantics. A matched result may legitimately carry `None` as its value.
- Keep synchronous and asynchronous APIs behaviorally aligned where both exist, including short-circuit evaluation and trace outcomes.
- Avoid global mutable state, hidden context providers, and implicit side effects.
- Use type annotations for public APIs and implementation code. Target Python 3.10 syntax and behavior.
- Keep formatting and lint rules in Ruff and typing strict under mypy; do not add local suppressions without a clear reason.

## Tests and quality checks

- Put tests under `tests/` and cover externally visible behavior, edge cases, and regressions.
- For synchronous and asynchronous counterparts, test parity where applicable.
- Preserve short-circuit behavior, no-match versus `None` payload distinction, and trace behavior when changing decision logic.
- The coverage report includes branch measurement and the configured minimum is 87%. Pytest writes terminal and XML reports.
- Before requesting review, run `make ci`. It runs Ruff lint and formatting checks, strict mypy, pytest with coverage, builds source and wheel distributions, and validates them with Twine.

## GitHub workflow

- Start feature work from an up-to-date `main` branch and use a focused branch and commit.
- Use the repository's SSH remote for Git operations and `gh` for pull request and CI operations.
- Open a pull request for completed changes. Include a concise description and the checks actually run.
- Before merging, confirm required checks pass, review feedback is addressed, and the PR is mergeable. Use the repository's established merge method.
- For long-running CI or other processes, use the `no-wait` skill: keep the process running and wait in longer intervals instead of repeatedly polling.
