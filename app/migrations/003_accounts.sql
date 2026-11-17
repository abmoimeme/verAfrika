-- Pilot accounts: invite-only password sign-in with TOTP MFA for staff.
-- Staging measure until the managed OIDC provider decision is made (LLD v1.4 §10, HLA §11).

ALTER TABLE users
  ADD COLUMN password_hash  text,
  ADD COLUMN mfa_secret     text,
  ADD COLUMN mfa_enabled    boolean NOT NULL DEFAULT false,
  ADD COLUMN mfa_last_step  bigint,
  ADD COLUMN failed_logins  integer NOT NULL DEFAULT 0,
  ADD COLUMN locked_until   timestamptz,
  ADD COLUMN last_login_at  timestamptz;
CREATE UNIQUE INDEX users_email_unique ON users (lower(email));

ALTER TABLE sessions
  ADD COLUMN mfa_verified boolean NOT NULL DEFAULT true,
  ADD COLUMN last_seen_at timestamptz NOT NULL DEFAULT now();

CREATE TABLE invites (
  token_hash      text PRIMARY KEY,
  email           text NOT NULL,
  organization_id text NOT NULL REFERENCES organizations(id),
  role_id         text NOT NULL REFERENCES roles(id),
  invited_by      text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  used_at         timestamptz,
  used_by         text REFERENCES users(id)
);
