"""VeraAfrika API — first vertical slice (modular monolith entry point)."""
from __future__ import annotations

import html
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import accounts, audit, auth, ingestion, opportunities, review
from .db import connect
from .errors import ApiError, invalid_request, not_visible

ROOT = Path(__file__).resolve().parent.parent
ENV = os.environ.get("VERAFRIKA_ENV", "development")
DEV = ENV == "development"
@asynccontextmanager
async def lifespan(_app):
    if os.environ.get("VERAFRIKA_AUTO_MIGRATE") == "1":
        from .seed import seed_base
        with connect() as conn:
            seed_base(conn)
    yield


app = FastAPI(title="VeraAfrika API", version="0.2.0-staging", lifespan=lifespan,
              docs_url="/docs" if DEV else None, redoc_url=None, openapi_url="/openapi.json" if DEV else None)
# Firebase Hosting forwards only a cookie named "__session" to Cloud Run, so the session cookie uses that name.
COOKIE = "__session"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")


def _client_ip(request: Request) -> str:
    if os.environ.get("VERAFRIKA_TRUST_PROXY") == "1":
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _allowed_hosts(request: Request) -> set[str]:
    """Hosts a cookie-authenticated write may come from: this request's Host, the public URL, and any configured
    front-end domains (Firebase Hosting reaches Cloud Run under the run.app host, not the browser's domain)."""
    hosts = {request.headers.get("host", "").lower()}
    public = os.environ.get("PUBLIC_BASE_URL", "")
    if "://" in public:
        hosts.add(public.split("://", 1)[1].split("/", 1)[0].lower())
    hosts |= {h.strip().lower() for h in os.environ.get("VERAFRIKA_ALLOWED_HOSTS", "").split(",") if h.strip()}
    hosts.discard("")
    return hosts


@app.middleware("http")
async def security(request: Request, call_next):
    # Cookie-authenticated writes must come from this site (CSRF defence in addition to SameSite cookies).
    if request.method not in SAFE_METHODS and request.cookies.get(COOKIE) and not request.headers.get("authorization"):
        origin = request.headers.get("origin") or request.headers.get("referer", "")
        if not origin or origin.split("://", 1)[-1].split("/", 1)[0].lower() not in _allowed_hosts(request):
            return JSONResponse(status_code=403, content={"error": {"code": "permission_denied", "message": "Cross-site request blocked.",
                                                                    "reason": "origin_mismatch"}})
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if not request.url.path.startswith("/docs"):
        resp.headers.setdefault("Content-Security-Policy", CSP)
    if not DEV:
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.url.path.startswith("/v1/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp


# Cloud Run reserves some paths ending in "z" (including /healthz), so /health is the probe used in production.
@app.get("/health")
@app.get("/healthz")
def healthz():
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "env": ENV}


def _set_session(resp: JSONResponse, token: str) -> JSONResponse:
    resp.set_cookie(COOKIE, token, httponly=True, samesite="lax" if not DEV else "strict", secure=not DEV,
                    max_age=accounts.SESSION_HOURS * 3600, path="/")
    return resp


# --- Pilot sign-in ------------------------------------------------------------------
@app.get("/v1/auth/config")
def auth_config():
    return {"mode": "dev" if DEV else "password", "env": ENV}


@app.post("/v1/auth/login")
def login(request: Request, payload: dict = Body(...)):
    if DEV and not os.environ.get("VERAFRIKA_ALLOW_PASSWORD_IN_DEV"):
        raise not_visible()
    with connect() as conn:
        out = accounts.login(conn, str(payload.get("email", "")), str(payload.get("password", "")), _client_ip(request))
    return _set_session(JSONResponse({"mfa": out["mfa"], "locale": out["locale"]}), out["token"])


@app.get("/v1/auth/mfa/setup")
def mfa_setup(request: Request):
    with connect() as conn:
        return accounts.mfa_setup(conn, _token(request))


@app.post("/v1/auth/mfa/verify")
def mfa_verify(request: Request, payload: dict = Body(...)):
    with connect() as conn:
        return accounts.mfa_verify(conn, _token(request), str(payload.get("code", "")), _client_ip(request))


@app.post("/v1/auth/logout")
def logout(request: Request):
    with connect() as conn:
        accounts.logout(conn, _token(request))
    resp = JSONResponse({"signed_out": True})
    resp.delete_cookie(COOKIE, path="/")
    return resp


@app.get("/v1/auth/invites/{token}")
def invite_info(token: str):
    with connect() as conn:
        return accounts.invite_info(conn, token)


@app.post("/v1/auth/invites/{token}/accept")
def accept_invite(token: str, payload: dict = Body(...)):
    with connect() as conn:
        out = accounts.accept_invite(conn, token, str(payload.get("display_name", "")), str(payload.get("password", "")),
                                     str(payload.get("locale", "fr")))
    return _set_session(JSONResponse({"mfa": out["mfa"]}), out["token"])


@app.exception_handler(ApiError)
async def api_error(_: Request, e: ApiError):
    return JSONResponse(status_code=e.status, content=e.body())


def _token(request: Request) -> str | None:
    h = request.headers.get("authorization", "")
    if h.lower().startswith("bearer "):
        return h[7:].strip()
    return request.cookies.get(COOKIE)


class Unit:
    """Request unit of work: resolves context on the server, commits on success."""

    def __init__(self, request: Request, permission: str | None = None):
        self.request, self.permission = request, permission

    def __enter__(self):
        self._cm = connect()
        self.conn = self._cm.__enter__()
        try:
            self.ctx = auth.resolve_context(self.conn, _token(self.request))
            if self.permission:
                auth.require(self.ctx, self.permission)
        except BaseException as e:
            # __exit__ is not called when __enter__ raises; release the connection here.
            self._cm.__exit__(type(e), e, e.__traceback__)
            raise
        return self

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


# --- Context and entitlements (LLD §6) ---------------------------------------
@app.get("/v1/me/context")
def me(request: Request):
    with Unit(request) as u:
        c = u.ctx
        orgs = u.conn.execute(
            "SELECT o.id, o.legal_name, o.kind FROM memberships m JOIN organizations o ON o.id=m.organization_id "
            "WHERE m.user_id=%s AND m.status='active' ORDER BY o.legal_name", (c.user_id,)).fetchall()
        return {"user": {"id": c.user_id, "display_name": c.display_name, "locale": c.locale},
                "organization": {"id": c.organization_id, "name": c.organization_name, "kind": c.organization_kind,
                                 "company_id": c.company_id},
                "role": c.role_key, "plan": c.plan_key, "organizations": orgs}


@app.post("/v1/context/organization")
def switch_org(request: Request, payload: dict = Body(...)):
    with Unit(request) as u:
        auth.switch_organization(u.conn, _token(request), u.ctx.user_id, str(payload.get("organization_id", "")))
        return {"organization_id": payload.get("organization_id")}


@app.get("/v1/entitlements")
def entitlements(request: Request):
    with Unit(request) as u:
        limits = {}
        if u.ctx.plan_key:
            for r in u.conn.execute("SELECT permission_key, limit_json FROM plan_entitlements WHERE plan_key=%s AND limit_json <> '{}'::jsonb",
                                    (u.ctx.plan_key,)):
                limits[r["permission_key"]] = r["limit_json"]
        usage = u.conn.execute("SELECT permission_key, period_start, period_end, used_count FROM entitlement_usage WHERE organization_id=%s "
                               "AND period_end > now()", (u.ctx.organization_id,)).fetchall()
        return {"plan": u.ctx.plan_key, "permissions": sorted(u.ctx.permissions), "limits": limits, "usage": usage}


@app.get("/v1/coverage")
def coverage(request: Request):
    with Unit(request, "source.coverage") as u:
        return {"coverage": u.conn.execute(
            "SELECT c.scope_type, c.country_code, c.onboarding_state, c.field_coverage, c.expected_cadence, c.last_success_at, "
            "s.name AS source_name, s.rights_status FROM country_source_coverage c LEFT JOIN sources s ON s.id=c.source_id "
            "ORDER BY c.country_code").fetchall()}


@app.get("/v1/reference/sector-taxonomy")
def taxonomy(request: Request, parent_code: str | None = None, level: str | None = None):
    with Unit(request) as u:
        if level == "activity" and not u.ctx.has("intelligence.custom"):
            auth.require(u.ctx, "intelligence.custom")
        t = u.conn.execute("SELECT id, version, checksum FROM sector_taxonomies WHERE activated_at IS NOT NULL AND retired_at IS NULL").fetchone()
        q, a = "SELECT code, level, parent_code, label FROM sector_nodes WHERE taxonomy_id=%s", [t["id"]]
        if parent_code:
            q += " AND parent_code=%s"; a.append(parent_code)
        else:
            q += " AND level=%s"; a.append(level or "sector")
        return {"version": t["version"], "checksum": t["checksum"], "nodes": u.conn.execute(q + " ORDER BY sort_order", a).fetchall()}


# --- Opportunities -------------------------------------------------------------
@app.get("/v1/opportunities")
def search(request: Request, country: str = "SN", q: str | None = None, industry_code: str | None = None):
    with Unit(request) as u:
        return opportunities.search(u.conn, u.ctx, country, q, industry_code)


@app.get("/v1/opportunities/{opp_id}")
def get_opportunity(request: Request, opp_id: str):
    with Unit(request) as u:
        return opportunities.get(u.conn, u.ctx, opp_id)


@app.put("/v1/opportunities/{opp_id}/saved")
def save(request: Request, opp_id: str):
    with Unit(request) as u:
        return opportunities.save(u.conn, u.ctx, opp_id, True)


@app.delete("/v1/opportunities/{opp_id}/saved")
def unsave(request: Request, opp_id: str):
    with Unit(request) as u:
        return opportunities.save(u.conn, u.ctx, opp_id, False)


@app.post("/v1/opportunities/{opp_id}/pursuits")
def create_pursuit(request: Request, opp_id: str, payload: dict | None = Body(default=None),
                   idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    with Unit(request) as u:
        status, body, replayed = opportunities.create_pursuit(u.conn, u.ctx, opp_id, idempotency_key, payload or {})
        return JSONResponse(status_code=status, content=json.loads(json.dumps(body, default=str)),
                            headers={"Idempotent-Replayed": "true" if replayed else "false"})


@app.get("/v1/pursuits")
def pursuits(request: Request):
    with Unit(request) as u:
        return {"pursuits": opportunities.list_pursuits(u.conn, u.ctx)}


@app.get("/v1/pursuits/{pursuit_id}")
def pursuit(request: Request, pursuit_id: str):
    with Unit(request) as u:
        return opportunities.get_pursuit(u.conn, u.ctx, pursuit_id)


@app.get("/v1/alerts")
def alerts(request: Request):
    with Unit(request) as u:
        rows = u.conn.execute(
            "SELECT a.id, a.kind, a.payload, a.opportunity_id, a.created_at, a.read_at, a.amendment_id, m.issuer_reference "
            "FROM alerts a LEFT JOIN amendments m ON m.id=a.amendment_id WHERE a.organization_id=%s ORDER BY a.created_at DESC LIMIT 50",
            (u.ctx.organization_id,)).fetchall()
        return {"alerts": rows, "unread": sum(1 for r in rows if not r["read_at"])}


@app.post("/v1/alerts/{alert_id}/read")
def read_alert(request: Request, alert_id: str):
    with Unit(request) as u:
        r = u.conn.execute("UPDATE alerts SET read_at=COALESCE(read_at, now()) WHERE id=%s AND organization_id=%s RETURNING id",
                           (alert_id, u.ctx.organization_id)).fetchone()
        if not r:
            raise not_visible()
        return {"id": alert_id, "read": True}


@app.get("/v1/audit/events")
def audit_events(request: Request, object_id: str | None = None, action: str | None = None, limit: int = 100):
    with Unit(request, "audit.read") as u:
        q, a = "SELECT * FROM audit_events WHERE true", []
        if object_id:
            q += " AND (object_id=%s OR details_json::text LIKE %s)"; a += [object_id, f"%{object_id}%"]
        if action:
            q += " AND action=%s"; a.append(action)
        return {"events": u.conn.execute(q + " ORDER BY id DESC LIMIT %s", a + [min(max(limit, 1), 500)]).fetchall()}


# --- Analyst operations ----------------------------------------------------------
@app.get("/v1/admin/sources")
def sources(request: Request):
    with Unit(request, "source.run") as u:
        return {"sources": u.conn.execute("SELECT id,key,name,owner,country_code,access_method,rights_status,rights_policy_version,"
                                          "attribution,is_synthetic FROM sources ORDER BY key").fetchall()}


@app.post("/v1/admin/sources/{source_key}/runs")
def run_source(request: Request, source_key: str, payload: dict = Body(default={})):
    with Unit(request, "source.run") as u:
        actor = u.ctx.user_id
    return ingestion.run(source_key, str(payload.get("snapshot", "initial")), actor)


@app.get("/v1/admin/ingestion-runs")
def runs(request: Request):
    with Unit(request, "source.run") as u:
        return {"runs": u.conn.execute("SELECT r.*, s.key AS source_key FROM ingestion_runs r JOIN sources s ON s.id=r.source_id "
                                       "ORDER BY started_at DESC LIMIT 50").fetchall()}


@app.get("/v1/admin/review-tasks")
def tasks(request: Request, status: str = "open"):
    with Unit(request, "review.read") as u:
        return {"tasks": review.list_tasks(u.conn, status)}


@app.get("/v1/admin/review-tasks/{task_id}")
def task(request: Request, task_id: str):
    with Unit(request, "review.read") as u:
        return review.task_detail(u.conn, task_id)


@app.post("/v1/admin/review-tasks/{task_id}/corrections")
def correct(request: Request, task_id: str, payload: dict = Body(...)):
    with Unit(request, "review.decide") as u:
        if "field" not in payload or "value" not in payload:
            raise invalid_request("field and value are required.")
        return review.correct_field(u.conn, task_id, payload["field"], payload["value"], payload.get("reason", ""), u.ctx.user_id)


@app.post("/v1/admin/review-tasks/{task_id}/approve")
def approve(request: Request, task_id: str, payload: dict = Body(default={})):
    with Unit(request, "review.decide") as u:
        return review.approve(u.conn, task_id, u.ctx.user_id, payload.get("note"))


@app.post("/v1/admin/review-tasks/{task_id}/reject")
def reject(request: Request, task_id: str, payload: dict = Body(default={})):
    with Unit(request, "review.decide") as u:
        return review.reject(u.conn, task_id, u.ctx.user_id, payload.get("note", ""))


@app.get("/v1/admin/opportunities")
def admin_opportunities(request: Request):
    with Unit(request, "trace.read") as u:
        return {"opportunities": u.conn.execute(
            "SELECT o.id, o.external_key, o.status, o.published_version, o.latest_version, o.last_seen_at, "
            "(SELECT a.value_json FROM opportunity_assertions a JOIN opportunity_versions v ON v.id=a.version_id "
            " WHERE v.opportunity_id=o.id AND v.version_no=o.latest_version AND a.field_path='title' AND a.superseded_by_id IS NULL) AS title "
            "FROM opportunities o ORDER BY o.created_at DESC").fetchall()}


@app.get("/v1/admin/opportunities/{opp_id}/trace")
def trace(request: Request, opp_id: str, field: str | None = None):
    with Unit(request, "trace.read") as u:
        out = review.trace(u.conn, opp_id, field)
        audit.record(u.conn, "opportunity.trace_viewed", actor_id=u.ctx.user_id, organization_id=u.ctx.organization_id,
                     object_type="opportunity", object_id=opp_id, field=field)
        return out


# --- Development only ------------------------------------------------------------
def _dev_only():
    if not DEV:
        raise not_visible()


@app.get("/v1/dev/personas")
def personas():
    _dev_only()
    with connect() as conn:
        return {"personas": conn.execute(
            "SELECT u.id, u.display_name, u.locale, o.legal_name AS organization, o.kind, r.key AS role, s.plan_key AS plan "
            "FROM users u JOIN memberships m ON m.user_id=u.id AND m.status='active' JOIN organizations o ON o.id=m.organization_id "
            "JOIN roles r ON r.id=m.role_id LEFT JOIN subscriptions s ON s.organization_id=o.id AND s.status='active' ORDER BY o.kind DESC, u.id").fetchall()}


@app.post("/v1/dev/sessions")
def dev_session(payload: dict = Body(...)):
    _dev_only()
    with connect() as conn:
        token = auth.issue_dev_session(conn, str(payload.get("user_id", "")))
    return _set_session(JSONResponse({"token": token}), token)


@app.post("/v1/dev/sign-out")
def sign_out():
    resp = JSONResponse({"signed_out": True})
    resp.delete_cookie(COOKIE)
    return resp


@app.get("/fixtures/sources/sn-synthetic/notices/{avis_id}", response_class=HTMLResponse)
def fixture_issuer_page(avis_id: str, rev: str = "1"):
    """The 'original source' page for the synthetic feed, standing in for an issuer's notice page."""
    if ENV == "production":
        raise not_visible()
    path = ROOT / "connectors" / "fixtures" / "sn_synthetic" / f"{avis_id}.rev{rev}.json"
    if not path.is_file() or path.parent != (ROOT / "connectors" / "fixtures" / "sn_synthetic"):
        raise not_visible()
    raw = json.loads(path.read_text())
    rows = "".join(f"<tr><th scope='row'>{html.escape(k)}</th><td>{html.escape(json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v)}</td></tr>"
                   for k, v in raw.items() if not k.startswith("_"))
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Avis {html.escape(avis_id)} — source synthétique</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;color:#17324D}}
.banner{{background:#FAF3E5;border:2px solid #8E6821;padding:.75rem 1rem;border-radius:6px}}
table{{border-collapse:collapse;width:100%}}th,td{{border-bottom:1px solid #8a96a3;padding:.5rem;text-align:left;vertical-align:top}}
th{{width:30%}}</style></head><body><main>
<p class="banner" role="note"><strong>Données de test synthétiques.</strong> {html.escape(raw.get('_fixture_notice',''))}</p>
<h1>Avis {html.escape(avis_id)} — révision {html.escape(rev)}</h1>
<table><caption class="visually-hidden">Contenu brut de l'avis</caption><tbody>{rows}</tbody></table></main></body></html>"""


WEB = ROOT / "web"
if WEB.is_dir():
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
