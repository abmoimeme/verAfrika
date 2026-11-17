"""VeraAfrika operations CLI.

  python -m app.cli init                         migrate and load reference data (any environment; idempotent)
  python -m app.cli reset                        drop everything and reseed with sample personas (development only)
  python -m app.cli load-samples                 add the fictional sample companies (development/staging demos)
  python -m app.cli create-org --name NAME --plan compete [--country SN] [--industry VA02.03.01] [--capabilities a,b]
  python -m app.cli invite --email E --org ORG_ID --role owner|viewer|analyst|auditor [--days 7]
  python -m app.cli reset-access --email E [--reset-mfa]   single-use link to set a new password (valid 2 days)
  python -m app.cli list-orgs
"""
from __future__ import annotations

import argparse
import os
import sys

from . import accounts
from .db import connect, dsn, new_id
from .seed import reset, seed_base, seed_samples

ENV = os.environ.get("VERAFRIKA_ENV", "development")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="app.cli", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("reset")
    sub.add_parser("load-samples")
    sub.add_parser("list-orgs")
    o = sub.add_parser("create-org")
    o.add_argument("--name", required=True)
    o.add_argument("--plan", required=True, choices=["discover", "compete", "grow", "enterprise"])
    o.add_argument("--country", default="SN")
    o.add_argument("--industry", action="append", default=[], help="VA industry code; repeatable")
    o.add_argument("--capabilities", default="", help="comma-separated capability tags, e.g. solar_pumping,water_supply")
    i = sub.add_parser("invite")
    i.add_argument("--email", required=True)
    i.add_argument("--org", required=True)
    i.add_argument("--role", required=True, choices=["owner", "viewer", "analyst", "auditor"])
    i.add_argument("--days", type=int, default=7)
    ra = sub.add_parser("reset-access")
    ra.add_argument("--email", required=True)
    ra.add_argument("--reset-mfa", action="store_true", help="also require a new authenticator set-up (lost phone)")
    a = ap.parse_args(argv)

    with connect() as conn:
        if a.cmd == "init":
            seed_base(conn)
            print(f"Database ready: {dsn().split('@')[-1]}")
        elif a.cmd == "reset":
            if ENV != "development":
                sys.exit("reset is only allowed when VERAFRIKA_ENV=development")
            reset(conn)
            print("Reset and seeded with sample personas.")
        elif a.cmd == "load-samples":
            if ENV == "production":
                sys.exit("Sample data is not allowed in production.")
            seed_base(conn)
            seed_samples(conn)
            print("Sample companies and personas loaded (dev sign-in personas cannot sign in outside development).")
        elif a.cmd == "list-orgs":
            for r in conn.execute("SELECT o.id, o.legal_name, o.kind, s.plan_key FROM organizations o LEFT JOIN subscriptions s "
                                  "ON s.organization_id=o.id AND s.status='active' ORDER BY o.kind DESC, o.legal_name"):
                print(f"{r['id']:<28} {r['kind']:<9} {r['plan_key'] or '-':<10} {r['legal_name']}")
        elif a.cmd == "create-org":
            cid, oid = new_id("vaf"), new_id("org")
            conn.execute("INSERT INTO companies(id,legal_name,country_code) VALUES (%s,%s,%s)", (cid, a.name, a.country.upper()))
            conn.execute("INSERT INTO company_profiles(company_id,sector_codes,capabilities) VALUES (%s,%s,%s)",
                         (cid, a.industry, [c.strip() for c in a.capabilities.split(",") if c.strip()]))
            conn.execute("INSERT INTO organizations(id,legal_name,country_code,tenant_key,kind,company_id) VALUES (%s,%s,%s,%s,'customer',%s)",
                         (oid, a.name, a.country.upper(), oid, cid))
            conn.execute("INSERT INTO subscriptions(id,organization_id,plan_key) VALUES (%s,%s,%s)", (new_id("sub"), oid, a.plan))
            print(f"Created {oid} ({a.plan}) linked to company {cid}. Registration status is unknown until verified.")
        elif a.cmd == "reset-access":
            token = accounts.create_reset(conn, a.email, a.reset_mfa, issued_by="cli")
            base = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8077").rstrip("/")
            print(f"Password reset link for {a.email} (valid 2 days, single use; existing sessions end when used):\n{base}/#/invite/{token}")
        elif a.cmd == "invite":
            token = accounts.create_invite(conn, a.email, a.org, a.role, invited_by="cli", days=a.days)
            base = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8077").rstrip("/")
            print(f"Invitation for {a.email} (valid {a.days} days, single use):\n{base}/#/invite/{token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
