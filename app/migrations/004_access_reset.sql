-- Single-use links that let an existing user set a new password (and optionally re-enrol MFA).
ALTER TABLE invites ADD COLUMN purpose text NOT NULL DEFAULT 'join' CHECK (purpose IN ('join','reset'));
ALTER TABLE invites ADD COLUMN reset_mfa boolean NOT NULL DEFAULT false;
ALTER TABLE invites ALTER COLUMN organization_id DROP NOT NULL;
ALTER TABLE invites ALTER COLUMN role_id DROP NOT NULL;
