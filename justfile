# Run all quality checks
check: format-check lint type-check test

# Run fast checks (skip tests)
check-fast: format-check lint type-check

# Fix auto-fixable issues
fix:
    ruff check --fix .
    ruff format .

# Check code formatting
format-check:
    ruff format --check .

# Run linter
lint:
    ruff check .

# Run type checker
type-check:
    uv run ty check

# Run tests
test:
    uv run pytest

# Run tests in verbose mode
test-verbose:
    uv run pytest -v

# Run tests with coverage
test-coverage:
    uv run pytest --cov=src/youtube_sync --cov-report=term-missing

# Watch tests
test-watch:
    uv run pytest-watcher

# Sync YouTube subscriptions to Feedbin (dry-run by default)
sync-subs:
    uv run python -m youtube_sync.jobs.sync_subs

# Actually sync subscriptions (makes real changes)
sync-subs-apply:
    uv run python -m youtube_sync.jobs.sync_subs --apply
