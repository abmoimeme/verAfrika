"""Customer-facing opportunity projections, saves and pursuits.

The API builds the authorized projection on the server. Fields a tier may not see are
never placed in the response (LLD v1.4 §4 critical production rule).
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone

from . import audit
from .auth import Context, require
from .db import Jsonb, new_id
from .errors import ApiError, idempotency_conflict, invalid_request, not_visible, usage_limit_reached
from .review import current_fields
from .taxonomy import label_path

IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9_\-:.]{16,128}$")


def _published(conn, opp_id: str) -> dict:
    opp = conn.execute(
        "SELECT o.*, s.name AS source_name, s.attribution, s.is_synthetic, s.owner AS source_owner "
        "FROM opportunities o JOIN sources s ON s.id=o.source_id WHERE o.id=%s AND o.status='published'", (opp_id,)
    ).fetchone()
    if not opp:
        raise not_visible()
    return opp


def project(conn, ctx: Context, opp: dict) -> dict:
    require(ctx, "opportunity.summary", object_type="opportunity", object_id=opp["id"])
    v = conn.execute(
        "SELECT v.*, r.retrieved_at, r.source_url, r.checksum, r.id AS record_id FROM opportunity_versions v "
        "JOIN source_records r ON r.id=v.source_record_id WHERE v.opportunity_id=%s AND v.version_no=%s",
        (opp["id"], opp["published_version"])).fetchone()
    f = current_fields(conn, v["id"])
    amendments = conn.execute(
        "SELECT a.*, v.review_state FROM amendments a JOIN opportunity_versions v ON v.opportunity_id=a.opportunity_id AND v.version_no=a.to_version "
        "WHERE a.opportunity_id=%s AND a.to_version<=%s ORDER BY a.to_version DESC", (opp["id"], opp["published_version"])).fetchall()
    pending_newer = opp["latest_version"] > opp["published_version"]
    last = amendments[0] if amendments else None

    out = {
        "id": opp["id"],
        "version": opp["published_version"],
        "title": f.get("title"),
        "issuer": f.get("issuer"),
        "country_code": opp["country_code"],
        "deadline": f.get("deadline"),
        "published_on": f.get("published_on"),
        "industry": label_path(conn, f.get("industry_code")),
        "verification": "issuer_amendment_pending_confirmation" if v["review_state"] == "published_pending_confirmation" else "analyst_reviewed",
        "amended": bool(amendments),
        "last_amendment": {"issuer_reference": last["issuer_reference"], "detected_at": last["detected_at"].isoformat(),
                           "changed_fields": [c["field"] for c in last["changed_fields"]]} if last else None,
        "newer_source_version_under_review": pending_newer,
        "source": {"name": opp["source_name"], "attribution": opp["attribution"],
                   "observed_at": v["retrieved_at"].isoformat(), "last_seen_at": opp["last_seen_at"].isoformat()},
        "sample_data": opp["is_synthetic"],
        "saved": bool(conn.execute("SELECT 1 FROM saved_opportunities WHERE organization_id=%s AND opportunity_id=%s",
                                   (ctx.organization_id, opp["id"])).fetchone()),
        "access": {"details": ctx.has("opportunity.details"), "provenance": ctx.has("source.provenance"),
                   "match": ctx.has("matching.score"), "pursuit": ctx.has("bid.workspace"), "save": ctx.has("opportunity.save")},
    }
    if ctx.has("opportunity.details"):
        out.update({
            "reference": f.get("reference"), "procedure": f.get("procedure"), "place": f.get("place"),
            "lots": f.get("lots"), "qualification_requirements": f.get("qualification_requirements"),
            "eligible_countries": f.get("eligible_countries"), "estimated_value": f.get("estimated_value"),
            "language": f.get("language"),
            "amendment_history": [{"issuer_reference": a["issuer_reference"], "detected_at": a["detected_at"].isoformat(),
                                   "to_version": a["to_version"], "changes": a["changed_fields"]} for a in amendments],
        })
    if ctx.has("source.provenance"):
        out["source"].update({"url": v["source_url"], "record_id": v["record_id"], "checksum": v["checksum"]})
    if ctx.has("matching.score") and ctx.company_id:
        m = conn.execute("SELECT * FROM matches WHERE opportunity_id=%s AND company_id=%s ORDER BY version_no DESC LIMIT 1",
                         (opp["id"], ctx.company_id)).fetchone()
        out["match"] = {k: m[k] for k in ("eligible", "score", "confidence", "strengths", "gaps", "limitations", "rule_version", "version_no")} if m else None
    p = conn.execute("SELECT id, status, created_at FROM pursuits WHERE organization_id=%s AND opportunity_id=%s AND status='active'",
                     (ctx.organization_id, opp["id"])).fetchone()
    out["pursuit"] = {"id": p["id"], "status": p["status"], "created_at": p["created_at"].isoformat()} if p else None
    return out


def get(conn, ctx: Context, opp_id: str) -> dict:
    out = project(conn, ctx, _published(conn, opp_id))
    if ctx.has("opportunity.details"):
        audit.record(conn, "opportunity.details_viewed", actor_id=ctx.user_id, organization_id=ctx.organization_id,
                     object_type="opportunity", object_id=opp_id, plan=ctx.plan_key)
    return out


def search(conn, ctx: Context, country: str = "SN", q: str | None = None, industry_code: str | None = None) -> dict:
    require(ctx, "opportunity.summary")
    country = (country or "").upper()
    if not re.fullmatch(r"[A-Z]{2}", country):
        raise invalid_request("Choose a country.", field="country")
    cov = conn.execute(
        "SELECT onboarding_state, last_success_at, expected_cadence FROM country_source_coverage WHERE scope_type='country' AND country_code=%s "
        "ORDER BY CASE onboarding_state WHEN 'active' THEN 0 WHEN 'degraded' THEN 1 ELSE 2 END LIMIT 1", (country,)).fetchone()
    coverage = {"country_code": country, "state": cov["onboarding_state"] if cov else "not_researched",
                "last_success_at": cov["last_success_at"].isoformat() if cov and cov["last_success_at"] else None,
                "expected_cadence": cov["expected_cadence"] if cov else None}
    if coverage["state"] not in ("active", "degraded"):
        return {"coverage": coverage, "results": [], "complete": False}
    sql = ("SELECT o.*, s.name AS source_name, s.attribution, s.is_synthetic, s.owner AS source_owner "
           "FROM opportunities o JOIN sources s ON s.id=o.source_id "
           "JOIN opportunity_versions v ON v.opportunity_id=o.id AND v.version_no=o.published_version "
           "WHERE o.status='published' AND o.country_code=%s")
    args: list = [country]
    if q:
        sql += (" AND EXISTS (SELECT 1 FROM opportunity_assertions a WHERE a.version_id=v.id AND a.superseded_by_id IS NULL "
                "AND a.field_path IN ('title','issuer','reference') AND a.value_json::text ILIKE %s)")
        args.append(f"%{q}%")
    if industry_code:
        sql += (" AND EXISTS (SELECT 1 FROM opportunity_assertions a WHERE a.version_id=v.id AND a.superseded_by_id IS NULL "
                "AND a.field_path='industry_code' AND (a.value_json #>> '{}') LIKE %s)")
        args.append(f"{industry_code}%")
    rows = conn.execute(sql + " ORDER BY o.created_at DESC LIMIT 50", args).fetchall()
    return {"coverage": coverage, "complete": True, "results": [project(conn, ctx, r) for r in rows]}


def save(conn, ctx: Context, opp_id: str, saved: bool) -> dict:
    require(ctx, "opportunity.save", object_type="opportunity", object_id=opp_id)
    _published(conn, opp_id)
    if saved:
        r = conn.execute("INSERT INTO saved_opportunities(organization_id,opportunity_id,saved_by) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING RETURNING 1",
                         (ctx.organization_id, opp_id, ctx.user_id)).fetchone()
        if r:
            audit.record(conn, "opportunity.saved", actor_id=ctx.user_id, organization_id=ctx.organization_id,
                         object_type="opportunity", object_id=opp_id)
    else:
        r = conn.execute("DELETE FROM saved_opportunities WHERE organization_id=%s AND opportunity_id=%s RETURNING 1",
                         (ctx.organization_id, opp_id)).fetchone()
        if r:
            audit.record(conn, "opportunity.unsaved", actor_id=ctx.user_id, organization_id=ctx.organization_id,
                         object_type="opportunity", object_id=opp_id)
    return {"opportunity_id": opp_id, "saved": saved}


def _month_bounds(today: date) -> tuple[date, date]:
    start = today.replace(day=1)
    end = (start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1))
    return start, end


def create_pursuit(conn, ctx: Context, opp_id: str, idem_key: str | None, body: dict) -> tuple[int, dict, bool]:
    """Returns (status, body, replayed). LLD v1.4 §6.2 idempotency contract."""
    if not idem_key or not IDEMPOTENCY_KEY.fullmatch(idem_key):
        raise invalid_request("An Idempotency-Key header of 16–128 characters is required.", field="Idempotency-Key")
    require(ctx, "bid.workspace", object_type="opportunity", object_id=opp_id)
    route = "POST /v1/opportunities/{id}/pursuits"
    req_hash = hashlib.sha256(json.dumps({"opportunity_id": opp_id, "body": body}, sort_keys=True).encode()).hexdigest()

    inserted = conn.execute(
        "INSERT INTO idempotency_requests(organization_id,route_key,idempotency_key,request_hash,status,expires_at) "
        "VALUES (%s,%s,%s,%s,'in_progress', now() + interval '24 hours') ON CONFLICT DO NOTHING RETURNING 1",
        (ctx.organization_id, route, idem_key, req_hash)).fetchone()
    if not inserted:
        prior = conn.execute("SELECT * FROM idempotency_requests WHERE organization_id=%s AND route_key=%s AND idempotency_key=%s",
                             (ctx.organization_id, route, idem_key)).fetchone()
        if prior["request_hash"] != req_hash:
            raise idempotency_conflict()
        if prior["status"] == "completed" and prior["expires_at"] > datetime.now(timezone.utc):
            return prior["response_code"], prior["response_body"], True
        raise ApiError(409, "idempotency_conflict", "The original request is still being processed. Try again shortly.")

    opp = _published(conn, opp_id)
    if not ctx.company_id:
        raise ApiError(422, "review_required", "Your organization is not yet linked to a company profile.")
    f = current_fields(conn, conn.execute("SELECT id FROM opportunity_versions WHERE opportunity_id=%s AND version_no=%s",
                                          (opp_id, opp["published_version"])).fetchone()["id"])
    if f.get("deadline") and datetime.fromisoformat(f["deadline"]) <= datetime.now(timezone.utc):
        raise ApiError(409, "opportunity_closed", "The submission deadline for this tender has passed.")
    existing = conn.execute("SELECT id FROM pursuits WHERE organization_id=%s AND opportunity_id=%s AND status='active'",
                            (ctx.organization_id, opp_id)).fetchone()
    if existing:
        raise ApiError(409, "pursuit_exists", "Your organization already has a bid workspace for this tender.", pursuit_id=existing["id"])
    if not ctx.has("bid.multiple"):
        lim = conn.execute("SELECT limit_json FROM plan_entitlements WHERE plan_key=%s AND permission_key='bid.workspace'", (ctx.plan_key,)).fetchone()
        max_active = (lim["limit_json"] or {}).get("max_active_pursuits") if lim else None
        active = conn.execute("SELECT count(*) AS n FROM pursuits WHERE organization_id=%s AND status='active'", (ctx.organization_id,)).fetchone()["n"]
        if max_active is not None and active >= max_active:
            raise usage_limit_reached("bid.workspace", max_active, None, "grow")

    pid = new_id("pur")
    conn.execute("INSERT INTO pursuits(id,organization_id,opportunity_id,company_id,created_by,opportunity_version) VALUES (%s,%s,%s,%s,%s,%s)",
                 (pid, ctx.organization_id, opp_id, ctx.company_id, ctx.user_id, opp["published_version"]))
    start, end = _month_bounds(date.today())
    conn.execute("INSERT INTO entitlement_usage(organization_id,permission_key,period_start,period_end,used_count) VALUES (%s,'bid.workspace',%s,%s,1) "
                 "ON CONFLICT (organization_id,permission_key,period_start) DO UPDATE SET used_count=entitlement_usage.used_count+1",
                 (ctx.organization_id, start, end))
    conn.execute("INSERT INTO saved_opportunities(organization_id,opportunity_id,saved_by) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                 (ctx.organization_id, opp_id, ctx.user_id))
    conn.execute("INSERT INTO alerts(id,organization_id,opportunity_id,kind,payload) VALUES (%s,%s,%s,'pursuit_started',%s)",
                 (new_id("alr"), ctx.organization_id, opp_id, Jsonb({"pursuit_id": pid, "deadline": f.get("deadline")})))
    audit.record(conn, "pursuit.created", actor_id=ctx.user_id, organization_id=ctx.organization_id, object_type="pursuit",
                 object_id=pid, opportunity_id=opp_id, opportunity_version=opp["published_version"], idempotency_key_hash=req_hash[:12])
    resp = {"id": pid, "opportunity_id": opp_id, "status": "active", "opportunity_version": opp["published_version"],
            "deadline": f.get("deadline"), "title": f.get("title")}
    conn.execute("UPDATE idempotency_requests SET status='completed', response_code=201, response_body=%s "
                 "WHERE organization_id=%s AND route_key=%s AND idempotency_key=%s",
                 (Jsonb(resp), ctx.organization_id, route, idem_key))
    return 201, resp, False


def get_pursuit(conn, ctx: Context, pursuit_id: str) -> dict:
    p = conn.execute("SELECT * FROM pursuits WHERE id=%s AND organization_id=%s", (pursuit_id, ctx.organization_id)).fetchone()
    if not p:
        audit.record(conn, "access.denied", actor_id=ctx.user_id, organization_id=ctx.organization_id,
                     object_type="pursuit", object_id=pursuit_id, reason="not_visible_to_tenant")
        conn.commit()
        raise not_visible()
    opp = project(conn, ctx, _published(conn, p["opportunity_id"]))
    return {"id": p["id"], "status": p["status"], "created_at": p["created_at"].isoformat(),
            "opportunity_version_at_start": p["opportunity_version"], "opportunity": opp}


def list_pursuits(conn, ctx: Context) -> list[dict]:
    rows = conn.execute("SELECT id FROM pursuits WHERE organization_id=%s ORDER BY created_at DESC", (ctx.organization_id,)).fetchall()
    return [get_pursuit(conn, ctx, r["id"]) for r in rows]
