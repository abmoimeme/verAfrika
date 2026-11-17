-- First vertical slice: ingestion, versioned opportunities, analyst review,
-- matching, saves, pursuits and alerts (HLA v1.4 §12.1).

CREATE TABLE ingestion_runs (
  id                    text PRIMARY KEY,
  source_id             text NOT NULL REFERENCES sources(id),
  rights_policy_version text NOT NULL,
  status                text NOT NULL CHECK (status IN ('running','succeeded','failed')),
  started_at            timestamptz NOT NULL DEFAULT now(),
  finished_at           timestamptz,
  records_seen          integer NOT NULL DEFAULT 0,
  records_new           integer NOT NULL DEFAULT 0,
  records_amended       integer NOT NULL DEFAULT 0,
  records_unchanged     integer NOT NULL DEFAULT 0,
  error                 text,
  triggered_by          text
);

-- Permitted raw record, preserved byte-for-byte as received (as JSON). Never updated.
CREATE TABLE source_records (
  id               text PRIMARY KEY,
  source_id        text NOT NULL REFERENCES sources(id),
  ingestion_run_id text NOT NULL REFERENCES ingestion_runs(id),
  external_key     text NOT NULL,
  source_url       text NOT NULL,
  retrieved_at     timestamptz NOT NULL,
  checksum         text NOT NULL,
  raw_json         jsonb NOT NULL,
  UNIQUE (source_id, external_key, checksum)
);
CREATE TRIGGER source_records_no_update BEFORE UPDATE OR DELETE ON source_records
  FOR EACH ROW EXECUTE FUNCTION audit_events_immutable();

CREATE TABLE opportunities (
  id                 text PRIMARY KEY,
  source_id          text NOT NULL REFERENCES sources(id),
  external_key       text NOT NULL,
  country_code       text NOT NULL,
  status             text NOT NULL CHECK (status IN ('pending_review','published','withdrawn')),
  published_version  integer,            -- version customers see
  latest_version     integer NOT NULL,   -- newest version from the source
  last_seen_at       timestamptz NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_id, external_key)
);

CREATE TABLE opportunity_versions (
  id               text PRIMARY KEY,
  opportunity_id   text NOT NULL REFERENCES opportunities(id),
  version_no       integer NOT NULL,
  source_record_id text NOT NULL REFERENCES source_records(id),
  review_state     text NOT NULL CHECK (review_state IN ('pending_review','published_pending_confirmation','approved','rejected')),
  created_at       timestamptz NOT NULL DEFAULT now(),
  published_at     timestamptz,
  reviewed_by      text REFERENCES users(id),
  reviewed_at      timestamptz,
  UNIQUE (opportunity_id, version_no)
);

-- Field-level assertions. Source values are never overwritten; analyst corrections
-- supersede them and keep the reason and actor.
CREATE TABLE opportunity_assertions (
  id               text PRIMARY KEY,
  version_id       text NOT NULL REFERENCES opportunity_versions(id),
  field_path       text NOT NULL,
  value_json       jsonb,
  origin           text NOT NULL CHECK (origin IN ('source','analyst')),
  source_record_id text REFERENCES source_records(id),
  actor_id         text REFERENCES users(id),
  reason           text,
  supersedes_id    text REFERENCES opportunity_assertions(id),
  superseded_by_id text REFERENCES opportunity_assertions(id) DEFERRABLE INITIALLY DEFERRED,
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX assertions_one_current ON opportunity_assertions(version_id, field_path) WHERE superseded_by_id IS NULL;

CREATE TABLE amendments (
  id                 text PRIMARY KEY,
  opportunity_id     text NOT NULL REFERENCES opportunities(id),
  from_version       integer NOT NULL,
  to_version         integer NOT NULL,
  issuer_reference   text,                -- e.g. "Additif n°1"
  changed_fields     jsonb NOT NULL,      -- [{field, old, new}]
  source_record_id   text NOT NULL REFERENCES source_records(id),
  ingestion_run_id   text NOT NULL REFERENCES ingestion_runs(id),
  detected_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE review_tasks (
  id             text PRIMARY KEY,
  opportunity_id text NOT NULL REFERENCES opportunities(id),
  version_id     text NOT NULL REFERENCES opportunity_versions(id),
  kind           text NOT NULL CHECK (kind IN ('new_notice','amendment')),
  priority       text NOT NULL CHECK (priority IN ('high','normal')),
  status         text NOT NULL DEFAULT 'open' CHECK (status IN ('open','approved','rejected')),
  due_at         timestamptz NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  resolved_at    timestamptz,
  resolved_by    text REFERENCES users(id),
  resolution_note text
);

CREATE TABLE matches (
  id             text PRIMARY KEY,
  opportunity_id text NOT NULL REFERENCES opportunities(id),
  version_no     integer NOT NULL,
  company_id     text NOT NULL REFERENCES companies(id),
  eligible       boolean NOT NULL,
  score          integer NOT NULL,
  confidence     text NOT NULL CHECK (confidence IN ('high','medium','low')),
  strengths      jsonb NOT NULL,
  gaps           jsonb NOT NULL,
  limitations    jsonb NOT NULL,
  rule_version   text NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (opportunity_id, version_no, company_id)
);

CREATE TABLE saved_opportunities (
  organization_id text NOT NULL REFERENCES organizations(id),
  opportunity_id  text NOT NULL REFERENCES opportunities(id),
  saved_by        text NOT NULL REFERENCES users(id),
  saved_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, opportunity_id)
);

CREATE TABLE pursuits (
  id              text PRIMARY KEY,
  organization_id text NOT NULL REFERENCES organizations(id),
  opportunity_id  text NOT NULL REFERENCES opportunities(id),
  company_id      text NOT NULL REFERENCES companies(id),
  created_by      text NOT NULL REFERENCES users(id),
  status          text NOT NULL DEFAULT 'active' CHECK (status IN ('active','withdrawn','submitted')),
  opportunity_version integer NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX pursuits_one_active ON pursuits(organization_id, opportunity_id) WHERE status = 'active';

CREATE TABLE alerts (
  id              text PRIMARY KEY,
  organization_id text NOT NULL REFERENCES organizations(id),
  opportunity_id  text REFERENCES opportunities(id),
  kind            text NOT NULL CHECK (kind IN ('deadline_changed','amendment_published','pursuit_started','new_match')),
  payload         jsonb NOT NULL,
  amendment_id    text REFERENCES amendments(id),
  delivery_status text NOT NULL DEFAULT 'delivered' CHECK (delivery_status IN ('pending','delivered','failed')),
  created_at      timestamptz NOT NULL DEFAULT now(),
  read_at         timestamptz,
  UNIQUE (organization_id, amendment_id, kind)
);
