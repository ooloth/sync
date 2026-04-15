# Architecture

youtube-sync is a Python CLI tool that syncs content between YouTube and other services. It runs as short-lived scripts (not a long-running server).

## Project structure

```
src/sync/
├── io/              # External service adapters (one folder per service)
│   ├── feedbin/
│   ├── op/          # 1Password CLI wrapper
│   ├── pushover/
│   ├── youtube/
│   ├── notion/      # Planned
│   └── sqlite/      # Planned
├── jobs/            # Entry points (one file per job)
│   ├── sync_subs.py
│   └── sync_likes.py
├── logging.py       # Structured logging configuration
└── types.py         # Shared type definitions
```

Jobs orchestrate I/O adapters. Adapters never call each other.

## I/O adapter pattern

Every integration in `io/` follows the same structure:

```
io/service_name/
├── auth.py          # Credentials (dataclass + create_auth_from_1password factory)
├── client.py        # API client class + create_client factory
├── models.py        # Pydantic response models (parsed at the I/O boundary)
└── tests/
    └── test_client.py
```

### Client conventions

- All client methods return `Result[T, ErrorMessage]` — never raise exceptions
- `ErrorMessage` is a `str` type alias defined in `types.py`
- Clients support three usage patterns: factory function (recommended), context manager, or manual `close()`
- Factory functions use `@lru_cache` and accept an optional auth parameter for test injection

```python
@lru_cache
def create_client(auth: ServiceAuth | None = None) -> ServiceClient:
    if auth is None:
        auth = create_auth_from_1password()
    return ServiceClient(auth)
```

## Error handling

Uses the `result` library (Rust-like `Ok`/`Err`). Client methods catch exceptions internally and return `Err(message)`. Jobs use `match` statements to handle results:

```python
match youtube.list_subscriptions():
    case Err(error):
        log.error("failed", error=error)
        return
    case Ok(subs):
        log.info("fetched", count=len(subs))
```

## Secrets management

All secrets live in 1Password (vault: "Scripts"). Retrieved at runtime via the `op` CLI through `io/op/secrets.py`:

```python
secret = get_secret("Feedbin", "password")  # op read op://Scripts/Feedbin/password
```

- Results are `@lru_cache`d per (item, field) pair
- Local dev: fingerprint authentication
- CI: `OP_SERVICE_ACCOUNT_TOKEN` environment variable

## Logging

Configured in `logging.py` using structlog + Rich:

- **Console**: Rich-formatted output to stderr, timestamps as `HH:MM:SS`
- **Files**: logfmt-style output in `.logs/` directory
  - `{job_name}.log` — all logs for that job
  - `errors.log` — ERROR+ from any job
  - `warnings.log` — WARNING only (not ERROR+)
- Logger names strip the `sync.` prefix for cleaner output
- Third-party loggers (httpx, httpcore, googleapiclient) silenced to WARNING

Jobs configure logging at startup:

```python
setup_logging(verbose=args.verbose, job_name="sync_subs")
```

## Testing

- pytest with tests co-located in each adapter's `tests/` folder
- HTTP mocking via pytest-httpx
- Response validation with inline-snapshot
- Auth fixtures inject credentials without hitting 1Password

## Tooling

| Tool        | Purpose                        |
| ----------- | ------------------------------ |
| uv          | Package/environment management |
| ruff        | Linting + formatting           |
| ty          | Type checking                  |
| hatchling   | Build backend                  |
| just        | Task runner (see `justfile`)   |
| Python 3.14 | Runtime                        |

Quality checks: `just check` (format, lint, type-check, test) or `just check-fast` (skip tests).
