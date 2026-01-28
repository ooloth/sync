from __future__ import annotations

import os
import sqlite3

from shell.adapters.db.user_repo_sqlite import SqliteUserRepo
from shell.adapters.event_bus.publisher_inmem import InMemoryPublisher  # simple dev default
from shell.contexts.base import AppContext


def create_context() -> AppContext:
    # dev-friendly default; can be overridden with env vars
    db_path = os.getenv("DEV_SQLITE_PATH", "./.local/dev.sqlite3")

    conn = sqlite3.connect(db_path, check_same_thread=False)
    users = SqliteUserRepo(conn)

    # In dev, using an in-memory publisher keeps things simple.
    # Swap to a real broker adapter when you want end-to-end event flow locally.
    events = InMemoryPublisher()

    return AppContext(users=users, events=events)
