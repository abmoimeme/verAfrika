"""Append-only audit events (LLD v1.4 §8). The table rejects UPDATE/DELETE at the database level."""
from __future__ import annotations

from .db import Jsonb


def record(conn, action: str, *, actor_id: str | None, organization_id: str | None,
           object_type: str | None = None, object_id: str | None = None, **details) -> None:
    conn.execute(
        "INSERT INTO audit_events(actor_id, organization_id, action, object_type, object_id, details_json) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (actor_id, organization_id, action, object_type, object_id, Jsonb(details)),
    )
