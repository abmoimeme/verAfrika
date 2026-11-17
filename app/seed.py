"""Development and test seed. All people, companies and notices are fictional sample data."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .auth import PLAN_INCREMENTS, PLAN_ORDER, plan_permissions
from .db import migrate
from .ingestion import TRACKED_FIELDS
from .taxonomy import import_and_activate

ROOT = Path(__file__).resolve().parent.parent
# Byte-identical copy of the handoff file (checksum verified in tests/test_vertical_slice.py).
TAXONOMY_CSV = ROOT / "reference" / "VERAFRIKA_sector_taxonomy_v1.csv"

AFRICAN_COUNTRIES = ("DZ AO BJ BW BF BI CV CM CF TD KM CG CD CI DJ EG GQ ER SZ ET GA GM GH GN GW KE LS LR LY MG MW ML MR MU "
                     "MA MZ NA NE NG RW ST SN SC SL SO ZA SS SD TZ TG TN UG ZM ZW").split()

ALL_CUSTOMER_PERMS = sorted({p for v in PLAN_INCREMENTS.values() for p in v})
VIEWER_PERMS = ["company.basic", "company.status", "opportunity.summary", "opportunity.details", "source.coverage",
                "source.provenance", "matching.score", "alert.weekly", "alert.deadline"]

PERSONAS = [
    # user id, name, email, locale, org, role
    ("usr_aminata", "Aminata Diallo", "aminata@sahel-solaire.example", "fr", "org_sahel", "role_owner"),
    ("usr_khady", "Khady Sarr", "khady@sahel-solaire.example", "fr", "org_sahel", "role_viewer"),
    ("usr_moussa", "Moussa Ndiaye", "moussa@teranga-forage.example", "fr", "org_teranga", "role_owner"),
    ("usr_awa", "Awa Mbaye", "awa@baobab-energie.example", "en", "org_baobab", "role_owner"),
    ("usr_fatou", "Fatou Ba", "fatou@verafrika.example", "en", "org_va_ops", "role_analyst"),
    ("usr_cheikh", "Cheikh Fall", "cheikh@verafrika.example", "en", "org_va_ops", "role_auditor"),
]


def seed(conn) -> None:
    """Development and tests: reference data plus sample companies and personas."""
    seed_base(conn)
    seed_samples(conn)


def seed_base(conn) -> None:
    """Reference data every environment needs: roles, plans, taxonomy, sources, coverage, operations org. Idempotent."""
    migrate(conn)
    if conn.execute("SELECT 1 FROM roles LIMIT 1").fetchone():
        return
    ex = conn.execute

    for rid, key, scope, desc in [
        ("role_owner", "owner", "customer", "Organization owner. All actions the plan grants."),
        ("role_viewer", "viewer", "customer", "Read-only member. Cannot save or start bids."),
        ("role_analyst", "analyst", "platform", "VeraAfrika data analyst. Reviews and publishes notices."),
        ("role_auditor", "auditor", "platform", "Reads the audit log and traces."),
    ]:
        ex("INSERT INTO roles VALUES (%s,%s,%s,%s)", (rid, key, scope, desc))
    for p in ALL_CUSTOMER_PERMS:
        ex("INSERT INTO role_permissions VALUES ('role_owner',%s)", (p,))
    for p in VIEWER_PERMS:
        ex("INSERT INTO role_permissions VALUES ('role_viewer',%s)", (p,))
    for p in ["review.read", "review.decide", "source.run", "trace.read", "opportunity.summary"]:
        ex("INSERT INTO role_permissions VALUES ('role_analyst',%s)", (p,))
    for p in ["audit.read", "trace.read"]:
        ex("INSERT INTO role_permissions VALUES ('role_auditor',%s)", (p,))

    for plan in PLAN_ORDER:
        for p in plan_permissions(plan):
            limit = '{"max_active_pursuits": 1}' if (plan == "compete" and p == "bid.workspace") else "{}"
            ex("INSERT INTO plan_entitlements VALUES (%s,%s,%s::jsonb)", (plan, p, limit))

    taxonomy = import_and_activate(conn, TAXONOMY_CSV)

    ex("INSERT INTO organizations(id,legal_name,country_code,tenant_key,kind) VALUES ('org_va_ops','VeraAfrika Operations','SN','va_ops','platform')")
    allowed = TRACKED_FIELDS + ["issuer_amendment"]
    ex("""INSERT INTO sources(id,key,name,owner,country_code,access_method,rights_status,rights_policy_version,allowed_fields,
          attribution,refresh_class,is_synthetic) VALUES
          ('src_sn_synthetic','sn-synthetic-procurement','Synthetic Senegal procurement feed (test data)',
           'VeraAfrika engineering — test fixture','SN','fixture:sn_synthetic','approved','fixture-2026-11',%s,
           'Synthetic test data. Not an official publication.','procurement_notices',true)""", (allowed,))
    ex("""INSERT INTO sources(id,key,name,owner,country_code,access_method,rights_status,rights_policy_version,allowed_fields,
          attribution,refresh_class,is_synthetic) VALUES
          ('src_sn_official_candidate','sn-official-procurement-candidate','Senegal official procurement source (candidate)',
           'To be confirmed by data partnerships and counsel','SN','not_configured','pending_review','none',%s,
           'Attribution to be defined in the source-rights decision.','procurement_notices',false)""", ([],))

    for cc in AFRICAN_COUNTRIES:
        if cc == "SN":
            ex("INSERT INTO country_source_coverage(scope_type,country_code,source_id,onboarding_state,field_coverage,expected_cadence) "
               "VALUES ('country','SN','src_sn_synthetic','active',%s,'every 4 hours')", (["opportunities", "amendments"],))
            ex("INSERT INTO country_source_coverage(scope_type,country_code,source_id,onboarding_state,field_coverage,expected_cadence) "
               "VALUES ('country','SN','src_sn_official_candidate','rights_review','{}','several times daily (planned)')")
        else:
            ex("INSERT INTO country_source_coverage(scope_type,country_code,onboarding_state) VALUES ('country',%s,'not_researched')", (cc,))
    assert len(AFRICAN_COUNTRIES) == 54, len(AFRICAN_COUNTRIES)
    _ = taxonomy


def seed_samples(conn) -> None:
    """Fictional sample companies, organizations and personas (development, tests and demos only)."""
    if conn.execute("SELECT 1 FROM users WHERE id='usr_aminata'").fetchone():
        return
    ex = conn.execute
    companies = [
        ("vaf_c1a7e2", "Sahel Solaire Services SARL (sample)", ["VA02.03.01", "VA02.01.01"], ["solar_pumping", "water_supply"], "SN-DKR-2019-B-10457", 10),
        ("vaf_c2b8f3", "Teranga Forage SUARL (sample)", ["VA02.03.01"], ["borehole_works", "water_supply"], "SN-THS-2021-A-02311", 40),
        ("vaf_c3c9a4", "Baobab Énergie SA (sample)", ["VA02.01.01"], ["solar_pumping"], "SN-DKR-2016-B-55120", 120),
    ]
    now = datetime.now(timezone.utc)
    for cid, name, sectors, caps, rccm, age_days in companies:
        ex("INSERT INTO companies(id,legal_name,country_code,is_sample) VALUES (%s,%s,'SN',true)", (cid, name))
        ex("INSERT INTO company_profiles(company_id,sector_codes,capabilities,locations) VALUES (%s,%s,%s,%s)",
           (cid, sectors, caps, ["Dakar"]))
        ex("INSERT INTO registrations VALUES (%s,%s,'SN','RCCM (sample)',%s,'active',%s)",
           (f"reg_{cid}", cid, rccm, now - timedelta(days=age_days)))

    for oid, name, kind, cid, plan in [
        ("org_sahel", "Sahel Solaire Services SARL (sample)", "customer", "vaf_c1a7e2", "compete"),
        ("org_teranga", "Teranga Forage SUARL (sample)", "customer", "vaf_c2b8f3", "discover"),
        ("org_baobab", "Baobab Énergie SA (sample)", "customer", "vaf_c3c9a4", "grow"),
    ]:
        ex("INSERT INTO organizations(id,legal_name,country_code,tenant_key,kind,company_id) VALUES (%s,%s,'SN',%s,%s,%s)",
           (oid, name, oid.replace("org_", ""), kind, cid))
        if plan:
            ex("INSERT INTO subscriptions(id,organization_id,plan_key) VALUES (%s,%s,%s)", (f"sub_{oid}", oid, plan))

    for uid, name, email, locale, org, role in PERSONAS:
        ex("INSERT INTO users(id,external_subject,display_name,email,locale) VALUES (%s,%s,%s,%s,%s)",
           (uid, f"dev|{uid}", name, email, locale))
        ex("INSERT INTO memberships(id,user_id,organization_id,role_id) VALUES (%s,%s,%s,%s)", (f"mem_{uid}", uid, org, role))



def reset(conn) -> None:
    """Drop and rebuild everything. Development and tests only."""
    conn.execute("DROP SCHEMA public CASCADE")
    conn.execute("CREATE SCHEMA public")
    seed(conn)
