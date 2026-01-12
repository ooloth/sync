# https://just.systems/man/en/introduction.html

check: format-check lint type-check test

check-fast: format-check lint type-check

fix:
    uv run ruff check --fix .
    uv run ruff format .

format-check:
    uv run ruff format --check .

lint:
    uv run ruff check .

type-check:
    uv run ty check

test:
    uv run pytest

test-verbose:
    uv run pytest -v

test-coverage:
    uv run pytest --cov=src/youtube_sync --cov-report=term-missing

test-watch:
    uv run pytest-watcher

sync-subs:
    uv run python -m youtube_sync.jobs.sync_subs

sync-subs-apply:
    uv run python -m youtube_sync.jobs.sync_subs --apply
