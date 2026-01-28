## File and folder names

### Top level

- `admin/deployment/` — deploy/run infra (optional but usually worth it in a monorepo)
- `admin/scripts/` — one-off admin/backfill tools (optional)
- `core/` — the functional core (rules + workflows + interfaces + contracts)
- `shell/` — the imperative shell (entrypoints + adapters + composition
- `tests/` — cross-cutting tests (service-local tests can still live near code if you prefer)

### Inside core/

- `core/applications/` — use cases / workflows (orchestration), no SDKs/frameworks
- `core/contracts/` — inter-service message schemas + envelope + versioning
- `core/domain/` — invariants, entities, value objects, domain events
- `core/ports/` — interfaces the core depends on

### Inside shell/

- `shell/adapters/` — outbound implementations (db, event bus, gcs, jira, etc.)
- `shell/contexts/` — environment-specific assembly of dependencies:
  - `base.py` defines `AppContext`
  - `dev.py`, `prod.py`, `test.py` provide `create\_\*\_context()` functions
- `shell/entrypoints/` — inbound (HTTP routes, event consumers, CLI, jobs)

### File naming conventions (helps discoverability more than layout)

- Use cases in `core/app/`: verb-y, action oriented:
  - `register_user.py`, `process_order_created.py`, `reconcile_invoice.py`
- Entrypoints mirror use cases by name (thin wrappers):
  - `shell/entrypoints/http/register_user.py`
  - `shell/entrypoints/events/register_user.py`
- Ports are nouns, capability oriented:
  - `user_repo.py`, `event_publisher.py`, `blob_store.py`, `clock.py`

### The one hard rule

- `core/` cannot import from `shell/` (ever)
- Everything else is negotiable.
- If you adopt just that naming + that rule, you’ll stay clean.
