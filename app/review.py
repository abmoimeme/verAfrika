"""Analyst review: queue, side-by-side raw record, corrections, publication, trace."""
from __future__ import annotations

from datetime import datetime, timezone

from . import audit, matching
from .db import Jsonb
from .errors import ApiError, invalid_request, not_visible
from .ingestion import _supersede

EDITABLE_FIELDS = {"title", "reference", "issuer", "procedure", "deadline", "place", "industry_code", "language"}


def current_fields(conn, version_id: str) -> dict:
    rows = conn.execute(
        "SELECT field_path, value_json FROM opportunity_assertions WHERE version_id=%s AND superseded_by_id IS NULL", (version_id,)
    ).fetchall()
    return {r["field_path"]: r["value_json"] for r in rows}


def list_tasks(conn, status: str = "open") -> list[dict]:
    rows = conn.execute(
        "SELECT t.*, v.version_no, v.review_state, o.external_key, o.country_code, "
        "(SELECT value_json FROM opportunity_assertions a WHERE a.version_id=t.version_id AND a.field_path='title' AND a.superseded_by_id IS NULL) AS title "
        "FROM review_tasks t JOIN opportunity_versions v ON v.id=t.version_id JOIN opportunities o ON o.id=t.opportunity_id "
        "WHERE t.status=%s ORDER BY CASE t.priority WHEN 'high' THEN 0 ELSE 1 END, t.due_at", (status,)
    ).fetchall()
    now = datetime.now(timezone.utc)
    for r in rows:
        r["overdue"] = r["due_at"] < now and r["status"] == "open"
    return rows


def task_detail(conn, task_id: str) -> dict:
    t = conn.execute("SELECT * FROM review_tasks WHERE id=%s", (task_id,)).fetchone()
    if not t:
        raise not_visible()
    v = conn.execute("SELECT * FROM opportunity_versions WHERE id=%s", (t["version_id"],)).fetchone()
    rec = conn.execute("SELECT id, source_url, retrieved_at, checksum, raw_json, ingestion_run_id FROM source_records WHERE id=%s",
                       (v["source_record_id"],)).fetchone()
    assertions = conn.execute(
        "SELECT id, field_path, value_json, origin, actor_id, reason, supersedes_id, superseded_by_id, created_at "
        "FROM opportunity_assertions WHERE version_id=%s ORDER BY field_path, created_at", (v["id"],)).fetchall()
    amendment = conn.execute("SELECT * FROM amendments WHERE opportunity_id=%s AND to_version=%s",
                             (t["opportunity_id"], v["version_no"])).fetchone()
    return {"task": t, "version": v, "source_record": rec, "fields": current_fields(conn, v["id"]),
            "assertions": assertions, "amendment": amendment}


def _open_task(conn, task_id):
    t = conn.execute("SELECT * FROM review_tasks WHERE id=%s FOR UPDATE", (task_id,)).fetchone()
    if not t:
        raise not_visible()
    if t["status"] != "open":
        raise ApiError(409, "task_closed", "This review task is already closed.", status=t["status"])
    return t


def correct_field(conn, task_id: str, field: str, value, reason: str, actor_id: str) -> dict:
    t = _open_task(conn, task_id)
    if field not in EDITABLE_FIELDS:
        raise invalid_request(f"Field '{field}' cannot be corrected here.", editable=sorted(EDITABLE_FIELDS))
    if not reason or len(reason.strip()) < 5:
        raise invalid_request("Give a reason for the correction (at least 5 characters).", field="reason")
    if field == "deadline":
        try:
            dt = datetime.fromisoformat(str(value))
        except ValueError:
            raise invalid_request("Deadline must be an ISO 8601 date and time, for example 2026-12-15T10:00:00+00:00.", field="value")
        if dt.tzinfo is None:
            raise invalid_request("Deadline must include a time zone.", field="value")
        value = dt.astimezone(timezone.utc).isoformat()
    if field == "industry_code":
        ok = conn.execute(
            "SELECT 1 FROM sector_nodes n JOIN sector_taxonomies s ON s.id=n.taxonomy_id WHERE s.activated_at IS NOT NULL "
            "AND s.retired_at IS NULL AND n.level='industry' AND n.code=%s", (value,)).fetchone()
        if not ok:
            raise invalid_request("Unknown industry code in the active taxonomy.", field="value")
    if field == "title" and not str(value).strip():
        raise invalid_request("Title cannot be empty.", field="value")
    aid = _supersede(conn, t["version_id"], field, value, reason.strip(), actor_id=actor_id)
    audit.record(conn, "opportunity.field_corrected", actor_id=actor_id, organization_id=None,
                 object_type="opportunity", object_id=t["opportunity_id"], field=field, assertion_id=aid, reason=reason.strip())
    return {"assertion_id": aid, "field": field, "value": value}


def approve(conn, task_id: str, actor_id: str, note: str | None = None) -> dict:
    t = _open_task(conn, task_id)
    v = conn.execute("SELECT * FROM opportunity_versions WHERE id=%s", (t["version_id"],)).fetchone()
    fields = current_fields(conn, v["id"])
    missing = [f for f in ("title", "issuer", "deadline", "reference") if not fields.get(f)]
    if missing:
        raise ApiError(422, "review_required", "Required fields are missing; correct them before publishing.", missing=missing)
    now = datetime.now(timezone.utc)
    conn.execute("UPDATE opportunity_versions SET review_state='approved', reviewed_by=%s, reviewed_at=%s, published_at=COALESCE(published_at,%s) WHERE id=%s",
                 (actor_id, now, now, v["id"]))
    opp = conn.execute("SELECT * FROM opportunities WHERE id=%s", (t["opportunity_id"],)).fetchone()
    newer_published = opp["published_version"] and opp["published_version"] > v["version_no"]
    if not newer_published:
        conn.execute("UPDATE opportunities SET status='published', published_version=%s WHERE id=%s", (v["version_no"], opp["id"]))
    conn.execute("UPDATE review_tasks SET status='approved', resolved_at=%s, resolved_by=%s, resolution_note=%s WHERE id=%s",
                 (now, actor_id, note, task_id))
    n = matching.compute_for_version(conn, opp["id"], v["version_no"], fields)
    # Interested organizations hear about reviewed amendments that were not auto-published.
    amendment = conn.execute("SELECT * FROM amendments WHERE opportunity_id=%s AND to_version=%s", (opp["id"], v["version_no"])).fetchone()
    if amendment and v["published_at"] is None and not newer_published:
        _alert(conn, opp["id"], amendment)
    audit.record(conn, "opportunity.review_approved", actor_id=actor_id, organization_id=None, object_type="opportunity",
                 object_id=opp["id"], version_no=v["version_no"], task_id=task_id, kind=t["kind"], matches_computed=n)
    return {"opportunity_id": opp["id"], "published_version": max(v["version_no"], opp["published_version"] or 0), "matches_computed": n}


def _alert(conn, opp_id, amendment):
    kind = "deadline_changed" if any(c["field"] == "deadline" for c in amendment["changed_fields"]) else "amendment_published"
    from .db import new_id
    for o in conn.execute(
        "SELECT organization_id FROM saved_opportunities WHERE opportunity_id=%s UNION "
        "SELECT organization_id FROM pursuits WHERE opportunity_id=%s AND status='active'", (opp_id, opp_id)).fetchall():
        conn.execute("INSERT INTO alerts(id,organization_id,opportunity_id,kind,payload,amendment_id) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                     (new_id("alr"), o["organization_id"], opp_id, kind, Jsonb({"changes": amendment["changed_fields"]}), amendment["id"]))


def reject(conn, task_id: str, actor_id: str, note: str) -> dict:
    t = _open_task(conn, task_id)
    v = conn.execute("SELECT * FROM opportunity_versions WHERE id=%s", (t["version_id"],)).fetchone()
    if v["review_state"] == "published_pending_confirmation":
        raise ApiError(409, "already_published",
                       "This issuer amendment is already visible to customers. Correct the field and approve instead.")
    if not note or len(note.strip()) < 5:
        raise invalid_request("Give a reason for rejecting (at least 5 characters).", field="note")
    now = datetime.now(timezone.utc)
    conn.execute("UPDATE opportunity_versions SET review_state='rejected', reviewed_by=%s, reviewed_at=%s WHERE id=%s", (actor_id, now, v["id"]))
    conn.execute("UPDATE review_tasks SET status='rejected', resolved_at=%s, resolved_by=%s, resolution_note=%s WHERE id=%s",
                 (now, actor_id, note.strip(), task_id))
    audit.record(conn, "opportunity.review_rejected", actor_id=actor_id, organization_id=None, object_type="opportunity",
                 object_id=t["opportunity_id"], version_no=v["version_no"], reason=note.strip())
    return {"task_id": task_id, "status": "rejected"}


def trace(conn, opp_id: str, field: str | None = None) -> dict:
    """Reconstruct a field back through assertions, source records, ingestion runs and amendments."""
    opp = conn.execute("SELECT * FROM opportunities WHERE id=%s", (opp_id,)).fetchone()
    if not opp:
        raise not_visible()
    versions = []
    for v in conn.execute("SELECT * FROM opportunity_versions WHERE opportunity_id=%s ORDER BY version_no", (opp_id,)).fetchall():
        rec = conn.execute("SELECT r.id, r.source_url, r.retrieved_at, r.checksum, r.ingestion_run_id, i.started_at AS run_started_at, i.status AS run_status "
                           "FROM source_records r JOIN ingestion_runs i ON i.id=r.ingestion_run_id WHERE r.id=%s", (v["source_record_id"],)).fetchone()
        q = "SELECT a.id, a.field_path, a.value_json, a.origin, a.actor_id, u.display_name AS actor_name, a.reason, a.supersedes_id, a.superseded_by_id, a.created_at " \
            "FROM opportunity_assertions a LEFT JOIN users u ON u.id=a.actor_id WHERE a.version_id=%s"
        args = [v["id"]]
        if field:
            q += " AND a.field_path=%s"
            args.append(field)
        versions.append({"version_no": v["version_no"], "review_state": v["review_state"], "published_at": v["published_at"],
                         "reviewed_by": v["reviewed_by"], "reviewed_at": v["reviewed_at"], "source_record": rec,
                         "assertions": conn.execute(q + " ORDER BY a.field_path, a.created_at", args).fetchall()})
    amendments = conn.execute("SELECT * FROM amendments WHERE opportunity_id=%s ORDER BY to_version", (opp_id,)).fetchall()
    return {"opportunity_id": opp_id, "published_version": opp["published_version"], "latest_version": opp["latest_version"],
            "field": field, "versions": versions, "amendments": amendments}
