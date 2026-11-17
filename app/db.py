"""Database access and migrations. PostgreSQL is the system of record (HLA §7.1)."""
from __future__ import annotations

import os
import secrets
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

MIGRATIONS = Path(__file__).parent / "migrations"


def dsn() -> str:
    return (os.environ.get("VERAFRIKA_DATABASE_URL") or os.environ.get("DATABASE_URL")
            or "postgresql://postgres@/verafrika?host=/tmp/pg&port=5433")


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(8)}"


@contextmanager
def connect():
    """One connection per unit of work; commits on success, rolls back on error."""
    with psycopg.connect(dsn(), row_factory=dict_row) as conn:
        yield conn


def migrate(conn) -> list[str]:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
    done = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}
    applied = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path.stem in done:
            continue
        sql = path.read_text().replace(
            "CREATE TABLE schema_migrations (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());", ""
        )
        conn.execute(sql)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (%s)", (path.stem,))
        applied.append(path.stem)
    return applied


__all__ = ["connect", "migrate", "new_id", "Jsonb", "dsn"]
