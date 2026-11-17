# VeraAfrika — first vertical slice

One procurement notice in one pilot market (Senegal), end to end:

```
approved source → raw record preserved → fields normalized → analyst reviews / corrects → published
→ entitled customer finds it, opens the original source, saves it, starts a bid
→ issuer amends the deadline → customer sees it and is alerted → analyst traces it to the amendment
```

This implements HLA v1.4 §12.1 and the LLD v1.4 contracts (identity context, entitlements, idempotent POSTs, provenance, append-only audit) as a modular monolith on PostgreSQL. **All data is synthetic or sample.** The notice and its issuer are fictional, and so are the companies and people.

## Layout

| Path | Contents |
|---|---|
| `app/` | FastAPI modular monolith: `auth` (context and authorization), `ingestion` (connector, normalization, versioning, amendments), `review` (analyst workflow, trace), `matching`, `opportunities` (customer projections, saves, pursuits), `taxonomy`, `audit` |
| `app/migrations/` | SQL schema. Audit events and raw source records are append-only at the database level |
| `connectors/fixtures/sn_synthetic/` | Synthetic notice: initial revision and "Additif n°1" (deadline moved to 12 Jan 2027) |
| `web/` | Pilot UI (customer, analyst, auditor), French and English |
| `tests/` | API acceptance tests; `tests/e2e/` browser journey with axe-core |
| `docs/UX_DESIGN_STANDARDS.md`, `CLAUDE.md`, `.claude/skills/ux-review/` | UX and QA framework |
| `reports/ux/` | UX review reports and e2e screenshots |
| `handoff/` | Original handoff snapshot. Checksummed; do not modify |

## Run it

Requires Python 3.11+ and PostgreSQL 14+.

```bash
pip install -r requirements-dev.txt
export VERAFRIKA_DATABASE_URL=postgresql://postgres@localhost:5432/verafrika
createdb verafrika && createdb verafrika_test
python3 -m app.cli reset
VERAFRIKA_ENV=development uvicorn app.main:app --port 8077
# open http://localhost:8077 and choose a test profile
```

**Demo path:**
1. Sign in as **Fatou Ba** (analyst). Go to Sources & runs and run the initial snapshot. Open the Review queue, correct a field if you like, then approve.
2. Sign in as **Aminata Diallo** (Compete). Open the tender, open the original source, save it, and start a bid.
3. Back as Fatou, run the "Additif n°1" snapshot.
4. As Aminata, check Alerts and the tender: you'll see the new deadline with the old one struck through.
5. As Fatou, open Trace to see the deadline chain back to the amendment.
6. Sign in as **Moussa Ndiaye** (Discover) to see the gated view. **Cheikh Fall** reads the audit log.

## Put it online (pilot staging)

See **[DEPLOY.md](DEPLOY.md)**. One container serves the API and the UI. `render.yaml` provisions it on Render with private PostgreSQL. Staging uses invite-only sign-in, with an authenticator app required for VeraAfrika staff. The development profile picker and API docs are off. People are onboarded with `python -m app.cli create-org | invite | reset-access`.

## Tests

```bash
VERAFRIKA_DATABASE_URL=postgresql://postgres@localhost:5432/verafrika_test pytest          # API acceptance suite
npm i axe-core && playwright install chromium
VERAFRIKA_E2E_URL=http://localhost:8077 AXE_PATH=node_modules/axe-core/axe.min.js pytest tests/e2e   # browser + axe (resets the dev DB)
```

## Decisions this slice made that need an owner

| Default in code | Why | Owner (from handoff decision register) |
|---|---|---|
| Deadline-only amendments from an approved source go live immediately, labeled "confirmation in progress", with a high-priority analyst task (4 h) | Stale deadlines are the top customer-trust risk (HLA §13) | Product + data lead |
| Compete allows 1 active bid workspace; Grow (`bid.multiple`) is unlimited | LLD lists `bid.multiple` only in Grow | Product + founder |
| Discover sees source name and observation date, but not the source link; Compete+ gets the link and record fingerprint | LLD §5.1 / `source.provenance` in Compete | Product |
| Raw records keep the issuer's contact fields for analysts; customers never receive them (not in `allowed_fields`) | LLD §7 permits raw preservation; contacts need rights review | Counsel + security |
| Development uses a profile picker. Staging uses invite-only email + password (scrypt), with TOTP required for staff. A managed OIDC provider remains the target | LLD §10, HLA §11 | Technical lead + security |
| Staging region placeholder: Frankfurt (`render.yaml`). Pilot accounts are personal data | LLD §10.1 `HOSTING_REGION` | Technical lead + counsel |

## Not built yet

- Any real source connector. The candidate official Senegal source is registered as `pending_review` and is blocked from running.
- OIDC and MFA, hosting region, evidence storage, notification delivery (email/WhatsApp), and bid workspace content.
- Company search, introductions, exports and the Trust Passport.
