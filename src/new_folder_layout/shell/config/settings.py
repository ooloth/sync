import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str  # "dev" | "prod" | "test"
    db_dsn: str
    broker: str
    gcs_bucket: str | None


def load_settings() -> Settings:
    env = os.getenv("APP_ENV", "dev")

    # Defaults are environment-specific, but still live here (shell).
    db_dsn = os.getenv("DB_DSN", "sqlite://./.local/dev.sqlite3")
    broker = os.getenv("BROKER", "inmem")  # e.g. "kafka://..."
    gcs_bucket = os.getenv("GCS_BUCKET")  # optional

    # minimal validation
    if env not in {"dev", "prod", "test"}:
        raise ValueError(f"Unknown APP_ENV: {env}")

    return Settings(env=env, db_dsn=db_dsn, broker=broker, gcs_bucket=gcs_bucket)
