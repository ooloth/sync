"""
This is the module where concrete implementations are chosen and glued together, connecting abstractions (ports) to
implementations (adapters).

It address three distinct needs in the "shell" layer at startup and shutdown:
  1. Choose implementations (Postgres vs SQLite, Kafka vs in-memory publisher, etc)
  2. Create them in the right order (config → DB connection → repo → use case deps)
  3. Control lifecycle (open connections, close connections, hooks for startup/shutdown)

It:
  1. Instantiates long-lived adapter dependencies
  2. Passes them into use cases / handlers as a struct-like object graph
  3. Loads config
  4. Manages lifecycle (startup/shutdown)

It’s a manually-built object graph:
  1. A struct-like object
  2. Holding long-lived dependencies
  3. Created once at startup
  4. Passed around implicitly (or imported)

This file is intentionally boring.
It:
  1. defines the shape of the runtime
  2. documents what the service depends on
  3. does not choose implementations
  4. does not do IO

"""

from dataclasses import dataclass

from core.ports.event_publisher import EventPublisher
from core.ports.user_repo import UserRepo


@dataclass(frozen=True)
class AppContext:
    """
    AppContext is the runtime dependency graph for this service.

    It contains concrete implementations of the ports required by the core.
    Entry points receive an AppContext and pass its members into use cases.
    """

    # Ports rather than adapters at this level (for typing)
    users: UserRepo
    events: EventPublisher
