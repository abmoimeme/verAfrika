"""Pilot accounts: invite-only sign-in, scrypt password hashes, TOTP MFA for staff.

Staging measure until a managed OIDC provider is chosen (decision register: identity provider).
Everything downstream (organization context, permissions, audit) is unchanged.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from . import audit
from .auth import hash_token
from .db import new_id
from .errors import ApiError, invalid_request

LOCK_AFTER = 5
LOCK_MINUTES = 15
IP_WINDOW_SECONDS = 600
IP_MAX_ATTEMPTS = 30
SESSION_HOURS = 8
COMMON = {"password1234", "motdepasse123", "123456789012", "azertyuiop12", "qwertyuiop12", "verafrika2026", "senegal123456"}

_ip_attempts: dict[str, deque] = defaultdict(deque)


# --- Passwords --------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=2**15, r=8, p=1, maxmem=64 * 1024 * 1024, dklen=32)
    return "scrypt$32768$8$1$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        # Constant-ish work so unknown emails take as long as known ones.
        hash_password(password)
        return False
    _, n, r, p, salt, dk = stored.split("$")
    test = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p),
                          maxmem=64 * 1024 * 1024, dklen=32)
    return hmac.compare_digest(test, base64.b64decode(dk))


def check_password_policy(password: str, email: str) -> None:
    if not isinstance(password, str) or len(password) < 12:
        raise invalid_request("Use at least 12 characters.", field="password", rule="min_length")
    if len(password) > 128:
        raise invalid_request("Use 128 characters or fewer.", field="password", rule="max_length")
    local = email.split("@")[0].lower()
    if password.lower() in COMMON or (len(local) >= 4 and local in password.lower()):
        raise invalid_request("Choose a less predictable password.", field="password", rule="predictable")


# --- TOTP (RFC 6238) -----------------------------------------------------------------
def new_totp_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode().rstrip("=")


def _hotp(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    h = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    o = h[-1] & 0x0F
    return f"{(struct.unpack('>I', h[o:o + 4])[0] & 0x7FFFFFFF) % 1_000_000:06d}"


def totp_now(secret: str, at: float | None = None) -> str:
    return _hotp(secret, int((at or time.time()) // 30))


def verify_totp(secret: str, code: str, last_step: int | None) -> int | None:
    """Returns the accepted time step, or None. Rejects replay of an already-used step."""
    code = "".join(ch for ch in str(code) if ch.isdigit())
    if len(code) != 6:
        return None
    now = int(time.time() // 30)
    for step in (now - 1, now, now + 1):
        if last_step is not None and step <= last_step:
            continue
        if hmac.compare_digest(_hotp(secret, step), code):
            return step
    return None


# --- Rate limiting ---------------------------------------------------------------------
def _ip_limited(ip: str) -> bool:
    q, now = _ip_attempts[ip], time.time()
    while q and q[0] < now - IP_WINDOW_SECONDS:
        q.popleft()
    q.append(now)
    return len(q) > IP_MAX_ATTEMPTS


def _too_many() -> ApiError:
    return ApiError(429, "too_many_attempts", "Too many sign-in attempts. Wait 15 minutes, then try again.", retry_after_minutes=LOCK_MINUTES)


# --- Sessions ---------------------------------------------------------------------------
def is_staff(conn, user_id: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM memberships m JOIN organizations o ON o.id=m.organization_id WHERE m.user_id=%s AND m.status='active' AND o.kind='platform'",
        (user_id,)).fetchone())


def issue_session(conn, user_id: str, mfa_verified: bool) -> str:
    org = conn.execute("SELECT organization_id FROM memberships WHERE user_id=%s AND status='active' ORDER BY id LIMIT 1", (user_id,)).fetchone()
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sessions(token_hash,user_id,active_org_id,expires_at,mfa_verified) VALUES (%s,%s,%s,%s,%s)",
                 (hash_token(token), user_id, org["organization_id"] if org else None,
                  datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS), mfa_verified))
    return token


def login(conn, email: str, password: str, ip: str) -> dict:
    if not email or not password:
        raise invalid_request("Enter your email and password.", field="email" if not email else "password")
    if _ip_limited(ip):
        raise _too_many()
    u = conn.execute("SELECT * FROM users WHERE lower(email)=lower(%s)", (email.strip(),)).fetchone()
    now = datetime.now(timezone.utc)
    if u and u["locked_until"] and u["locked_until"] > now:
        audit.record(conn, "auth.login_blocked", actor_id=u["id"], organization_id=None, reason="locked")
        conn.commit()
        raise _too_many()
    if not u or u["status"] != "active" or not verify_password(password, u["password_hash"] if u else None):
        if u:
            fails = u["failed_logins"] + 1
            conn.execute("UPDATE users SET failed_logins=%s, locked_until=%s WHERE id=%s",
                         (fails, now + timedelta(minutes=LOCK_MINUTES) if fails >= LOCK_AFTER else None, u["id"]))
            audit.record(conn, "auth.login_failed", actor_id=u["id"], organization_id=None, failed_count=fails)
            conn.commit()
        raise ApiError(401, "invalid_credentials", "Email or password is incorrect.")
    conn.execute("UPDATE users SET failed_logins=0, locked_until=NULL, last_login_at=now() WHERE id=%s", (u["id"],))
    staff = is_staff(conn, u["id"])
    token = issue_session(conn, u["id"], mfa_verified=not staff)
    audit.record(conn, "auth.login_succeeded", actor_id=u["id"], organization_id=None, mfa_pending=staff)
    return {"token": token, "mfa": ("verify" if u["mfa_enabled"] else "setup") if staff else None, "locale": u["locale"]}


def pending_session(conn, token: str | None) -> dict:
    if not token:
        raise ApiError(401, "authentication_required", "Sign in to continue.")
    s = conn.execute("SELECT s.*, u.mfa_secret, u.mfa_enabled, u.email, u.id AS uid FROM sessions s JOIN users u ON u.id=s.user_id "
                     "WHERE s.token_hash=%s AND s.expires_at > now()", (hash_token(token),)).fetchone()
    if not s:
        raise ApiError(401, "authentication_required", "Sign in to continue.")
    return s


def mfa_setup(conn, token: str | None) -> dict:
    s = pending_session(conn, token)
    if s["mfa_enabled"]:
        raise ApiError(409, "mfa_already_enabled", "Two-step verification is already set up for this account.")
    secret = s["mfa_secret"] or new_totp_secret()
    if not s["mfa_secret"]:
        conn.execute("UPDATE users SET mfa_secret=%s WHERE id=%s", (secret, s["uid"]))
    uri = f"otpauth://totp/VeraAfrika:{quote(s['email'])}?secret={secret}&issuer=VeraAfrika&digits=6&period=30"
    return {"secret": " ".join(secret[i:i + 4] for i in range(0, len(secret), 4)), "otpauth_uri": uri}


def mfa_verify(conn, token: str | None, code: str, ip: str) -> dict:
    s = pending_session(conn, token)
    if _ip_limited(ip):
        raise _too_many()
    if not s["mfa_secret"]:
        raise ApiError(409, "mfa_setup_required", "Set up two-step verification first.")
    row = conn.execute("SELECT mfa_last_step FROM users WHERE id=%s", (s["uid"],)).fetchone()
    step = verify_totp(s["mfa_secret"], code, row["mfa_last_step"])
    if step is None:
        audit.record(conn, "auth.mfa_failed", actor_id=s["uid"], organization_id=None)
        conn.commit()
        raise ApiError(401, "invalid_code", "That code didn't work. Enter the current 6-digit code from your authenticator app.")
    first = not s["mfa_enabled"]
    conn.execute("UPDATE users SET mfa_enabled=true, mfa_last_step=%s WHERE id=%s", (step, s["uid"]))
    conn.execute("UPDATE sessions SET mfa_verified=true WHERE token_hash=%s", (hash_token(token),))
    audit.record(conn, "auth.mfa_enabled" if first else "auth.mfa_verified", actor_id=s["uid"], organization_id=None)
    return {"verified": True}


def logout(conn, token: str | None) -> None:
    if token:
        conn.execute("UPDATE sessions SET expires_at=now() WHERE token_hash=%s", (hash_token(token),))


# --- Invites -----------------------------------------------------------------------------
def create_invite(conn, email: str, organization_id: str, role_key: str, invited_by: str | None, days: int = 7) -> str:
    role = conn.execute("SELECT r.id, r.scope, o.kind FROM roles r, organizations o WHERE r.key=%s AND o.id=%s",
                        (role_key, organization_id)).fetchone()
    if not role:
        raise invalid_request("Unknown organization or role.")
    if (role["scope"] == "platform") != (role["kind"] == "platform"):
        raise invalid_request("That role doesn't apply to this organization.")
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO invites(token_hash,email,organization_id,role_id,invited_by,expires_at) VALUES (%s,%s,%s,%s,%s,%s)",
                 (hash_token(token), email.strip().lower(), organization_id, role["id"], invited_by,
                  datetime.now(timezone.utc) + timedelta(days=days)))
    audit.record(conn, "auth.invite_created", actor_id=invited_by, organization_id=organization_id, email=email.strip().lower(), role=role_key)
    return token


def create_reset(conn, email: str, reset_mfa: bool, issued_by: str | None, days: int = 2) -> str:
    u = conn.execute("SELECT id FROM users WHERE lower(email)=lower(%s)", (email.strip(),)).fetchone()
    if not u:
        raise invalid_request("No account with this email.")
    conn.execute("UPDATE invites SET expires_at=now() WHERE lower(email)=lower(%s) AND purpose='reset' AND used_at IS NULL", (email.strip(),))
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO invites(token_hash,email,purpose,reset_mfa,invited_by,expires_at) VALUES (%s,%s,'reset',%s,%s,%s)",
                 (hash_token(token), email.strip().lower(), reset_mfa, issued_by, datetime.now(timezone.utc) + timedelta(days=days)))
    audit.record(conn, "auth.reset_issued", actor_id=issued_by, organization_id=None, user_id=u["id"], reset_mfa=reset_mfa)
    return token


def _invite(conn, token: str) -> dict:
    inv = conn.execute("SELECT i.*, o.legal_name, r.key AS role_key FROM invites i LEFT JOIN organizations o ON o.id=i.organization_id "
                       "LEFT JOIN roles r ON r.id=i.role_id WHERE i.token_hash=%s", (hash_token(token or ""),)).fetchone()
    if not inv or inv["used_at"] or inv["expires_at"] < datetime.now(timezone.utc):
        raise ApiError(404, "invite_invalid", "This invitation link is invalid or has expired. Ask your VeraAfrika contact for a new one.")
    return inv


def invite_info(conn, token: str) -> dict:
    inv = _invite(conn, token)
    return {"email": inv["email"], "organization": inv["legal_name"], "role": inv["role_key"], "purpose": inv["purpose"]}


def accept_invite(conn, token: str, display_name: str, password: str, locale: str) -> dict:
    inv = _invite(conn, token)
    if inv["purpose"] == "reset":
        return _complete_reset(conn, inv, token, password)
    if not display_name or not display_name.strip():
        raise invalid_request("Enter your name.", field="display_name")
    check_password_policy(password, inv["email"])
    if conn.execute("SELECT 1 FROM users WHERE lower(email)=lower(%s)", (inv["email"],)).fetchone():
        raise ApiError(409, "account_exists", "An account already exists for this email. Sign in instead, or ask for help.")
    uid = new_id("usr")
    conn.execute("INSERT INTO users(id,external_subject,display_name,email,locale,password_hash) VALUES (%s,%s,%s,%s,%s,%s)",
                 (uid, f"local|{uid}", display_name.strip()[:120], inv["email"], locale if locale in ("fr", "en") else "fr", hash_password(password)))
    conn.execute("INSERT INTO memberships(id,user_id,organization_id,role_id) VALUES (%s,%s,%s,%s)",
                 (new_id("mem"), uid, inv["organization_id"], inv["role_id"]))
    conn.execute("UPDATE invites SET used_at=now(), used_by=%s WHERE token_hash=%s", (uid, hash_token(token)))
    audit.record(conn, "auth.invite_accepted", actor_id=uid, organization_id=inv["organization_id"], role=inv["role_key"])
    staff = is_staff(conn, uid)
    session = issue_session(conn, uid, mfa_verified=not staff)
    return {"token": session, "mfa": "setup" if staff else None, "locale": locale}


def _complete_reset(conn, inv: dict, token: str, password: str) -> dict:
    check_password_policy(password, inv["email"])
    u = conn.execute("SELECT id FROM users WHERE lower(email)=lower(%s)", (inv["email"],)).fetchone()
    if not u:
        raise ApiError(404, "invite_invalid", "This link is invalid or has expired.")
    conn.execute("UPDATE users SET password_hash=%s, failed_logins=0, locked_until=NULL" +
                 (", mfa_enabled=false, mfa_secret=NULL, mfa_last_step=NULL" if inv["reset_mfa"] else "") + " WHERE id=%s",
                 (hash_password(password), u["id"]))
    conn.execute("UPDATE sessions SET expires_at=now() WHERE user_id=%s AND expires_at > now()", (u["id"],))
    conn.execute("UPDATE invites SET used_at=now(), used_by=%s WHERE token_hash=%s", (u["id"], hash_token(token)))
    audit.record(conn, "auth.password_reset", actor_id=u["id"], organization_id=None, reset_mfa=inv["reset_mfa"])
    staff = is_staff(conn, u["id"])
    session = issue_session(conn, u["id"], mfa_verified=not staff)
    mfa_on = conn.execute("SELECT mfa_enabled FROM users WHERE id=%s", (u["id"],)).fetchone()["mfa_enabled"]
    return {"token": session, "mfa": ("verify" if mfa_on else "setup") if staff else None, "locale": None}
