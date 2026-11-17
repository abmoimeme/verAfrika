"""Pilot sign-in: invites, password policy, lockout, staff MFA, CSRF and security headers."""
import time

import pytest

from app import accounts
from app.db import connect

ORIGIN = {"Origin": "http://testserver"}


@pytest.fixture(autouse=True)
def allow_password(monkeypatch):
    monkeypatch.setenv("VERAFRIKA_ALLOW_PASSWORD_IN_DEV", "1")
    accounts._ip_attempts.clear()


def invite(email, org, role):
    with connect() as c:
        return accounts.create_invite(c, email, org, role, invited_by="test")


def accept(client, token, password="un mot de passe solide", name="Awa Test"):
    return client.post(f"/v1/auth/invites/{token}/accept", json={"display_name": name, "password": password, "locale": "fr"}, headers=ORIGIN)


def test_customer_invite_creates_account_and_session(client):
    tok = invite("pilot@client.example", "org_sahel", "owner")
    assert client.get(f"/v1/auth/invites/{tok}").json()["organization"].startswith("Sahel")
    r = accept(client, tok)
    assert r.status_code == 200 and r.json()["mfa"] is None
    assert "httponly" in r.headers["set-cookie"].lower()
    me = client.get("/v1/me/context").json()
    assert me["organization"]["id"] == "org_sahel" and me["plan"] == "compete"
    # single use
    assert accept(client, tok).status_code == 404


def test_password_policy(client):
    tok = invite("short@client.example", "org_sahel", "viewer")
    r = accept(client, tok, password="tooshort")
    assert r.status_code == 400 and r.json()["error"]["field"] == "password"
    r = accept(client, tok, password="short@client.example-short")
    assert r.status_code == 400 and r.json()["error"]["rule"] == "predictable"


def test_login_and_lockout(client):
    accept(client, invite("lock@client.example", "org_sahel", "owner"))
    client.cookies.clear()
    ok = client.post("/v1/auth/login", json={"email": "LOCK@client.example", "password": "un mot de passe solide"}, headers=ORIGIN)
    assert ok.status_code == 200
    client.cookies.clear()
    for _ in range(5):
        r = client.post("/v1/auth/login", json={"email": "lock@client.example", "password": "wrong password here"}, headers=ORIGIN)
        assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_credentials"
    r = client.post("/v1/auth/login", json={"email": "lock@client.example", "password": "un mot de passe solide"}, headers=ORIGIN)
    assert r.status_code == 429
    unknown = client.post("/v1/auth/login", json={"email": "nobody@client.example", "password": "whatever-password"}, headers=ORIGIN)
    assert unknown.status_code == 401 and unknown.json()["error"]["message"] == "Email or password is incorrect."


def test_staff_must_complete_mfa(client):
    r = accept(client, invite("analyst@verafrika.example", "org_va_ops", "analyst"))
    assert r.json()["mfa"] == "setup"
    blocked = client.get("/v1/admin/review-tasks")
    assert blocked.status_code == 401 and blocked.json()["error"]["code"] == "mfa_required"
    setup = client.get("/v1/auth/mfa/setup").json()
    secret = setup["secret"].replace(" ", "")
    assert setup["otpauth_uri"].startswith("otpauth://totp/VeraAfrika:")
    assert client.post("/v1/auth/mfa/verify", json={"code": "000000"}, headers=ORIGIN).status_code == 401
    code = accounts.totp_now(secret)
    assert client.post("/v1/auth/mfa/verify", json={"code": code}, headers=ORIGIN).status_code == 200
    assert client.get("/v1/admin/review-tasks").status_code == 200
    # New sign-in: verification required again, and the same code cannot be replayed.
    client.cookies.clear()
    r = client.post("/v1/auth/login", json={"email": "analyst@verafrika.example", "password": "un mot de passe solide"}, headers=ORIGIN)
    assert r.json()["mfa"] == "verify"
    assert client.post("/v1/auth/mfa/verify", json={"code": code}, headers=ORIGIN).status_code == 401
    nxt = accounts._hotp(secret, int(time.time() // 30) + 1)
    assert client.post("/v1/auth/mfa/verify", json={"code": nxt}, headers=ORIGIN).status_code == 200


def test_cookie_writes_require_same_origin(client, published):
    opp_id, _ = published
    accept(client, invite("csrf@client.example", "org_sahel", "owner"))
    r = client.put(f"/v1/opportunities/{opp_id}/saved")
    assert r.status_code == 403 and r.json()["error"]["reason"] == "origin_mismatch"
    r = client.put(f"/v1/opportunities/{opp_id}/saved", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert client.put(f"/v1/opportunities/{opp_id}/saved", headers=ORIGIN).status_code == 200


def test_logout_ends_session(client):
    accept(client, invite("out@client.example", "org_sahel", "owner"))
    assert client.post("/v1/auth/logout", headers=ORIGIN).status_code == 200
    client.cookies.clear()
    assert client.get("/v1/me/context").status_code == 401


def test_security_headers(client):
    r = client.get("/healthz")
    assert r.json()["status"] == "ok"
    for h in ("content-security-policy", "x-content-type-options", "x-frame-options", "referrer-policy"):
        assert h in r.headers, h


def test_dev_personas_cannot_password_login(client):
    r = client.post("/v1/auth/login", json={"email": "aminata@sahel-solaire.example", "password": "anything-long-enough"}, headers=ORIGIN)
    assert r.status_code == 401


def test_reset_access_sets_new_password_and_ends_sessions(client):
    accept(client, invite("reset@client.example", "org_sahel", "owner"))
    old_cookie = dict(client.cookies)
    with connect() as c:
        tok = accounts.create_reset(c, "reset@client.example", reset_mfa=False, issued_by="test")
    client.cookies.clear()
    assert client.get(f"/v1/auth/invites/{tok}").json()["purpose"] == "reset"
    r = client.post(f"/v1/auth/invites/{tok}/accept", json={"password": "a brand new passphrase"}, headers=ORIGIN)
    assert r.status_code == 200
    client.cookies.clear()
    client.cookies.update(old_cookie)
    assert client.get("/v1/me/context").status_code == 401          # earlier session ended
    client.cookies.clear()
    ok = client.post("/v1/auth/login", json={"email": "reset@client.example", "password": "a brand new passphrase"}, headers=ORIGIN)
    assert ok.status_code == 200
    assert client.post(f"/v1/auth/invites/{tok}/accept", json={"password": "another passphrase!"}, headers=ORIGIN).status_code == 404


def test_reset_with_mfa_requires_new_authenticator(client):
    accept(client, invite("staff2@verafrika.example", "org_va_ops", "analyst"))
    secret = client.get("/v1/auth/mfa/setup").json()["secret"].replace(" ", "")
    client.post("/v1/auth/mfa/verify", json={"code": accounts.totp_now(secret)}, headers=ORIGIN)
    with connect() as c:
        tok = accounts.create_reset(c, "staff2@verafrika.example", reset_mfa=True, issued_by="test")
    client.cookies.clear()
    r = client.post(f"/v1/auth/invites/{tok}/accept", json={"password": "lost my phone passphrase"}, headers=ORIGIN)
    assert r.json()["mfa"] == "setup"


def test_session_cookie_name_survives_firebase_hosting(client):
    r = accept(client, invite("cookie@client.example", "org_sahel", "owner"))
    assert r.headers["set-cookie"].startswith("__session=")


def test_origin_check_accepts_configured_front_end_domain(client, published, monkeypatch):
    """Firebase Hosting → Cloud Run: Host is the run.app address, Origin is the web.app domain."""
    opp_id, _ = published
    accept(client, invite("fb@client.example", "org_sahel", "owner"))
    run_host = {"Host": "verafrika-staging-abc-ew.a.run.app"}
    r = client.put(f"/v1/opportunities/{opp_id}/saved", headers={**run_host, "Origin": "https://verafrika.web.app"})
    assert r.status_code == 403
    monkeypatch.setenv("VERAFRIKA_ALLOWED_HOSTS", "verafrika.web.app,verafrika.firebaseapp.com")
    r = client.put(f"/v1/opportunities/{opp_id}/saved", headers={**run_host, "Origin": "https://verafrika.web.app"})
    assert r.status_code == 200
    r = client.put(f"/v1/opportunities/{opp_id}/saved", headers={**run_host, "Origin": "https://verafrika.web.app.evil.example"})
    assert r.status_code == 403
