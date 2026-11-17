-- VeraAfrika shared foundation (LLD v1.4 §3.1, §3.2, §8)
-- Identity, tenancy, entitlements, idempotency, audit, company identity, taxonomy, coverage.

CREATE TABLE schema_migrations (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());

-- Identity and tenancy -------------------------------------------------------
CREATE TABLE users (
  id               text PRIMARY KEY,
  external_subject text NOT NULL UNIQUE,
  display_name     text NOT NULL,
  email            text NOT NULL,
  locale           text NOT NULL DEFAULT 'fr',
  status           text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','deleted')),
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE organizations (
  id           text PRIMARY KEY,
  legal_name   text NOT NULL,
  country_code text NOT NULL,
  tenant_key   text NOT NULL UNIQUE,
  kind         text NOT NULL CHECK (kind IN ('customer','platform')),
  company_id   text,                       -- the canonical company this customer org acts for
  status       text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended'))
);

CREATE TABLE roles (
  id          text PRIMARY KEY,
  key         text NOT NULL UNIQUE,
  scope       text NOT NULL CHECK (scope IN ('customer','platform')),
  description text NOT NULL
);

-- For customer roles this is a ceiling applied to plan permissions ("roles limit how they may be used").
-- For platform roles it is the grant itself.
CREATE TABLE role_permissions (
  role_id        text NOT NULL REFERENCES roles(id),
  permission_key text NOT NULL,
  PRIMARY KEY (role_id, permission_key)
);

CREATE TABLE memberships (
  id              text PRIMARY KEY,
  user_id         text NOT NULL REFERENCES users(id),
  organization_id text NOT NULL REFERENCES organizations(id),
  role_id         text NOT NULL REFERENCES roles(id),
  status          text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','revoked'))
);
CREATE UNIQUE INDEX memberships_one_active ON memberships(user_id, organization_id) WHERE status = 'active';

-- Development stand-in for managed OIDC sessions. Only token hashes are stored.
CREATE TABLE sessions (
  token_hash      text PRIMARY KEY,
  user_id         text NOT NULL REFERENCES users(id),
  active_org_id   text REFERENCES organizations(id),
  created_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL
);

CREATE TABLE subscriptions (
  id              text PRIMARY KEY,
  organization_id text NOT NULL REFERENCES organizations(id),
  plan_key        text NOT NULL CHECK (plan_key IN ('discover','compete','grow','enterprise')),
  status          text NOT NULL DEFAULT 'active' CHECK (status IN ('active','ended')),
  starts_at       timestamptz NOT NULL DEFAULT now(),
  ends_at         timestamptz
);
CREATE UNIQUE INDEX subscriptions_one_active ON subscriptions(organization_id) WHERE status = 'active';

CREATE TABLE plan_entitlements (
  plan_key       text NOT NULL,
  permission_key text NOT NULL,
  limit_json     jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (plan_key, permission_key)
);

CREATE TABLE contract_overrides (
  organization_id text NOT NULL REFERENCES organizations(id),
  permission_key  text NOT NULL,
  effect          text NOT NULL CHECK (effect IN ('allow','deny')),
  conditions_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (organization_id, permission_key)
);

CREATE TABLE entitlement_usage (
  organization_id text NOT NULL REFERENCES organizations(id),
  permission_key  text NOT NULL,
  period_start    date NOT NULL,
  period_end      date NOT NULL,
  used_count      integer NOT NULL DEFAULT 0,
  PRIMARY KEY (organization_id, permission_key, period_start)
);

CREATE TABLE idempotency_requests (
  organization_id text NOT NULL REFERENCES organizations(id),
  route_key       text NOT NULL,
  idempotency_key text NOT NULL,
  request_hash    text NOT NULL,
  status          text NOT NULL CHECK (status IN ('in_progress','completed')),
  response_code   integer,
  response_body   jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  PRIMARY KEY (organization_id, route_key, idempotency_key)
);

-- Audit (append-only) --------------------------------------------------------
CREATE TABLE audit_events (
  id              bigserial PRIMARY KEY,
  actor_id        text,
  organization_id text,
  action          text NOT NULL,
  object_type     text,
  object_id       text,
  details_json    jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_events_object ON audit_events(object_type, object_id);
CREATE INDEX audit_events_org ON audit_events(organization_id, occurred_at);

CREATE FUNCTION audit_events_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'audit_events is append-only';
END $$;
CREATE TRIGGER audit_events_no_update BEFORE UPDATE OR DELETE ON audit_events
  FOR EACH ROW EXECUTE FUNCTION audit_events_immutable();
CREATE TRIGGER audit_events_no_truncate BEFORE TRUNCATE ON audit_events
  FOR EACH STATEMENT EXECUTE FUNCTION audit_events_immutable();

-- Company identity -----------------------------------------------------------
CREATE TABLE companies (
  id           text PRIMARY KEY,           -- vaf_* non-semantic identifier
  legal_name   text NOT NULL,
  country_code text NOT NULL,
  status       text NOT NULL DEFAULT 'active',
  is_sample    boolean NOT NULL DEFAULT false,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE registrations (
  id                  text PRIMARY KEY,
  company_id          text NOT NULL REFERENCES companies(id),
  jurisdiction        text NOT NULL,
  authority           text NOT NULL,
  registration_number text NOT NULL,
  status              text NOT NULL CHECK (status IN ('active','inactive','suspended','dissolved','struck_off','unknown')),
  observed_at         timestamptz NOT NULL,
  UNIQUE (jurisdiction, registration_number)
);

CREATE TABLE company_profiles (
  company_id   text PRIMARY KEY REFERENCES companies(id),
  sector_codes text[] NOT NULL DEFAULT '{}',
  capabilities text[] NOT NULL DEFAULT '{}',
  locations    text[] NOT NULL DEFAULT '{}',
  projection_version integer NOT NULL DEFAULT 1
);

-- Sector taxonomy (LLD §5.4) --------------------------------------------------
CREATE TABLE sector_taxonomies (
  id            text PRIMARY KEY,
  key           text NOT NULL,
  version       text NOT NULL,
  source_file   text NOT NULL,
  checksum      text NOT NULL,
  rights_status text NOT NULL,
  activated_at  timestamptz,
  retired_at    timestamptz,
  UNIQUE (key, version)
);
CREATE UNIQUE INDEX sector_taxonomies_one_active ON sector_taxonomies(key) WHERE activated_at IS NOT NULL AND retired_at IS NULL;

CREATE TABLE sector_nodes (
  taxonomy_id text NOT NULL REFERENCES sector_taxonomies(id),
  code        text NOT NULL,
  level       text NOT NULL CHECK (level IN ('sector','cluster','industry','activity')),
  parent_code text,
  label       text NOT NULL,
  sort_order  integer NOT NULL,
  market_fit  text,
  is_active   boolean NOT NULL DEFAULT true,
  PRIMARY KEY (taxonomy_id, code)
);

-- Sources and coverage --------------------------------------------------------
CREATE TABLE sources (
  id               text PRIMARY KEY,
  key              text NOT NULL UNIQUE,
  name             text NOT NULL,
  owner            text NOT NULL,
  country_code     text NOT NULL,
  access_method    text NOT NULL,
  rights_status    text NOT NULL CHECK (rights_status IN ('approved','pending_review','denied')),
  rights_policy_version text NOT NULL,
  allowed_fields   text[] NOT NULL,
  attribution      text NOT NULL,
  refresh_class    text NOT NULL,
  is_synthetic     boolean NOT NULL DEFAULT false,
  auto_publish_deadline_amendments boolean NOT NULL DEFAULT true
);

CREATE TABLE country_source_coverage (
  scope_type       text NOT NULL CHECK (scope_type IN ('country','external_demand')),
  country_code     text NOT NULL,
  source_id        text REFERENCES sources(id),
  onboarding_state text NOT NULL CHECK (onboarding_state IN ('not_researched','discovery','rights_review','connector_development','active','degraded','suspended','retired')),
  field_coverage   text[] NOT NULL DEFAULT '{}',
  expected_cadence text,
  last_success_at  timestamptz,
  next_run_at      timestamptz
);
CREATE UNIQUE INDEX coverage_scope ON country_source_coverage(scope_type, country_code, COALESCE(source_id, ''));
