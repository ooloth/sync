# https://just.systems/man/en/introduction.html

check: format-check lint type-check test

check-fast: format-check lint type-check

dev:
    uv run pytest-watcher --now --clear src

doctor:
    # Validate dev environment setup
    uv run python scripts/doctor.py

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

sync-subs:
    uv run python -m youtube_sync.jobs.sync_subs

sync-subs-apply:
    uv run python -m youtube_sync.jobs.sync_subs --apply

sync-subs-verbose:
    uv run python -m youtube_sync.jobs.sync_subs --verbose
