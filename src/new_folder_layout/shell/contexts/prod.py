"""
Example usage in shell/entrypoints/http/register_user_handler.py:

from shell.composition.prod import create_context
from core.app.register_user import register_user, RegisterUserCommand

ctx = create_context()

def handle_http_request(payload: dict):
    cmd = RegisterUserCommand(email=payload["email"])
    return register_user(cmd, users=ctx.users, events=ctx.events)
"""

import sqlite3

from shell.adapters.db.user_repo_sqlite import SqliteUserRepo
from shell.adapters.event_bus.publisher_kafka import KafkaPublisher  # hypothetical
from shell.contexts.base import AppContext


def create_context() -> AppContext:
    conn = sqlite3.connect("/var/db/users.sqlite", check_same_thread=False)

    users = SqliteUserRepo(conn)
    events = KafkaPublisher(brokers=["kafka:9092"])

    # Adapters rather than ports now
    return AppContext(users=users, events=events)
