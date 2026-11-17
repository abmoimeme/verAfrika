"""Request context and server-side authorization (LLD v1.4 §4, §10).

Production replaces the development session issuer with managed OIDC. Everything downstream
(active organization, membership check, permission evaluation) stays the same: the browser
never supplies organization, role or plan.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from . import audit
from .db import connect
from .errors import ApiError, authentication_required, not_visible, permission_denied

PLAN_ORDER = ["discover", "compete", "grow", "enterprise"]

# LLD v1.4 §4 permission vocabulary, incremental by tier.
PLAN_INCREMENTS = {
    "discover": ["company.basic", "company.status", "opportunity.summary", "source.coverage", "alert.weekly"],
    "compete": ["opportunity.details", "opportunity.save", "matching.score", "bid.workspace",
                "verification.starter", "source.provenance", "alert.deadline"],
    "grow": ["company.contacts", "partner.discovery", "partner.introduction", "verification.passport",
             "research.full", "logistics.signals", "bid.multiple", "analyst.priority"],
    "enterprise": ["organization.teams", "organization.roles", "intelligence.custom", "data.export",
                   "signal.export", "api.access", "portfolio.reporting"],
}


def plan_permissions(plan: str) -> list[str]:
    perms: list[str] = []
    for p in PLAN_ORDER[: PLAN_ORDER.index(plan) + 1]:
        perms += PLAN_INCREMENTS[p]
    return perms


def required_plan_for(permission: str) -> str | None:
    for p in PLAN_ORDER:
        if permission in PLAN_INCREMENTS[p]:
            return p
    return None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass
class Context:
    user_id: str
    display_name: str
    locale: str
    organization_id: str
    organization_name: str
    organization_kind: str
    company_id: str | None
    role_key: str
    plan_key: str | None
    permissions: set[str] = field(default_factory=set)

    def has(self, perm: str) -> bool:
        return perm in self.permissions


def issue_dev_session(conn, user_id: str, org_id: str | None = None) -> str:
    if os.environ.get("VERAFRIKA_ENV", "development") != "development":
        raise ApiError(404, "resource_not_visible", "Not found.")
    if org_id is None:
        row = conn.execute(
            "SELECT organization_id FROM memberships WHERE user_id=%s AND status='active' ORDER BY id LIMIT 1", (user_id,)
        ).fetchone()
        org_id = row["organization_id"] if row else None
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO sessions(token_hash,user_id,active_org_id,expires_at) VALUES (%s,%s,%s,%s)",
        (hash_token(token), user_id, org_id, datetime.now(timezone.utc) + timedelta(hours=8)),
    )
    return token


def _record_denial(actor_id, org_id, permission, reason, object_type=None, object_id=None):
    # Denials must survive the rollback of the request transaction, so they use their own connection.
    with connect() as c:
        audit.record(c, "access.denied", actor_id=actor_id, organization_id=org_id,
                     object_type=object_type, object_id=object_id, permission=permission, reason=reason)


def resolve_context(conn, token: str | None) -> Context:
    if not token:
        raise authentication_required()
    s = conn.execute(
        "SELECT s.user_id, s.active_org_id, s.expires_at, s.mfa_verified, u.display_name, u.locale, u.status "
        "FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=%s",
        (hash_token(token),),
    ).fetchone()
    if not s or s["expires_at"] < datetime.now(timezone.utc) or s["status"] != "active":
        raise authentication_required()
    if not s["mfa_verified"]:
        raise ApiError(401, "mfa_required", "Enter the code from your authenticator app to continue.")
    m = conn.execute(
        "SELECT m.status, r.key AS role_key, r.id AS role_id, o.id AS org_id, o.legal_name, o.kind, o.company_id, o.status AS org_status "
        "FROM memberships m JOIN roles r ON r.id=m.role_id JOIN organizations o ON o.id=m.organization_id "
        "WHERE m.user_id=%s AND m.organization_id=%s AND m.status='active'",
        (s["user_id"], s["active_org_id"]),
    ).fetchone()
    if not m or m["org_status"] != "active":
        _record_denial(s["user_id"], s["active_org_id"], "organization.access", "membership_inactive")
        raise permission_denied("organization.access", reason="membership_inactive")

    role_perms = {r["permission_key"] for r in conn.execute(
        "SELECT permission_key FROM role_permissions WHERE role_id=%s", (m["role_id"],))}
    plan_key = None
    if m["kind"] == "platform":
        perms = role_perms
    else:
        sub = conn.execute(
            "SELECT plan_key FROM subscriptions WHERE organization_id=%s AND status='active'", (m["org_id"],)
        ).fetchone()
        plan_key = sub["plan_key"] if sub else None
        granted = {r["permission_key"] for r in conn.execute(
            "SELECT permission_key FROM plan_entitlements WHERE plan_key=%s", (plan_key,))} if plan_key else set()
        perms = granted & role_perms  # role is a ceiling on what the plan grants
        for o in conn.execute("SELECT permission_key, effect FROM contract_overrides WHERE organization_id=%s", (m["org_id"],)):
            if o["effect"] == "deny":
                perms.discard(o["permission_key"])
            elif o["permission_key"] in role_perms:
                perms.add(o["permission_key"])
    return Context(
        user_id=s["user_id"], display_name=s["display_name"], locale=s["locale"],
        organization_id=m["org_id"], organization_name=m["legal_name"], organization_kind=m["kind"],
        company_id=m["company_id"], role_key=m["role_key"], plan_key=plan_key, permissions=perms,
    )


def require(ctx: Context, permission: str, *, object_type: str | None = None, object_id: str | None = None) -> None:
    if ctx.has(permission):
        return
    plan = required_plan_for(permission) if ctx.organization_kind == "customer" else None
    reason = "plan_entitlement_missing" if plan and permission not in plan_permissions_ceiling(ctx) else "role_not_permitted"
    _record_denial(ctx.user_id, ctx.organization_id, permission, reason, object_type, object_id)
    if ctx.organization_kind == "customer" and reason == "plan_entitlement_missing":
        raise permission_denied(permission, required_plan=plan, reason=reason)
    # Staff routes are not disclosed to customer organizations, and vice versa.
    if permission.startswith(("review.", "source.run", "trace.", "audit.")) and ctx.organization_kind == "customer":
        raise not_visible()
    raise permission_denied(permission, reason=reason)


def plan_permissions_ceiling(ctx: Context) -> set[str]:
    return set(plan_permissions(ctx.plan_key)) if ctx.plan_key else set()


def switch_organization(conn, token: str, user_id: str, org_id: str) -> None:
    ok = conn.execute(
        "SELECT 1 FROM memberships WHERE user_id=%s AND organization_id=%s AND status='active'", (user_id, org_id)
    ).fetchone()
    if not ok:
        _record_denial(user_id, org_id, "organization.switch", "no_active_membership")
        raise permission_denied("organization.switch", reason="no_active_membership")
    conn.execute("UPDATE sessions SET active_org_id=%s WHERE token_hash=%s", (org_id, hash_token(token)))
    audit.record(conn, "context.organization_changed", actor_id=user_id, organization_id=org_id)
