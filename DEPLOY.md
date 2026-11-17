# Deploying VeraAfrika pilot staging

Staging runs one container: the API and pilot UI together, plus a managed PostgreSQL database. Sign-in works by invitation only. VeraAfrika staff must use an authenticator app (TOTP); pilot customers sign in with email and password. The development profile picker, sample personas and API docs are all disabled outside development.

> **Data notice.** The tender in staging is synthetic test data. Accounts are real: names and emails of pilot users are personal data. The hosting region is still an open decision (LLD §10.1, `HOSTING_REGION`). `render.yaml` uses Frankfurt as a placeholder until counsel confirms the Senegal CDP / transfer position.

## Option A — Render (recommended for the pilot)

1. Push this repository to a **private** GitHub repo. Leave out `handoff/` if you don't want the archive on GitHub; the server doesn't need it.
2. In Render, choose **New → Blueprint**, select the repo and confirm. `render.yaml` creates:
   - `verafrika-staging-db`: PostgreSQL 16, private network only.
   - `verafrika-staging`: a Docker web service with a `/healthz` health check. Auto-deploy is off, so every deploy is deliberate.
3. When asked for `PUBLIC_BASE_URL`, enter the service URL (for example `https://verafrika-staging.onrender.com`). You can also set it after the first deploy.
4. Deploy. On start the container applies migrations and loads reference data: roles, plans, the VA taxonomy, sources, coverage for all 54 countries, and the VeraAfrika Operations organization.
5. Check `https://<service>/healthz` returns `{"status":"ok","env":"staging"}`.

## Option B — Google Cloud Run

Build the image (`docker build -t verafrika-staging .`) and push it to Artifact Registry. Deploy it to Cloud Run with `DATABASE_URL` pointing at a Cloud SQL for PostgreSQL 16 instance; use the Cloud SQL connector or a private IP. Set `VERAFRIKA_ENV=staging` and `PUBLIC_BASE_URL`. The container listens on `$PORT`.

## Onboarding people

Run these from the service's shell (Render dashboard → Shell, or a one-off job). Each invitation link is single-use and valid for 7 days. Send it to the person yourself; email delivery isn't built yet.

```bash
# 1. First VeraAfrika staff member (analyst); sets up an authenticator app on first sign-in
python -m app.cli invite --email you@yourdomain --org org_va_ops --role analyst
python -m app.cli invite --email auditor@yourdomain --org org_va_ops --role auditor

# 2. Each pilot customer: create their organization (linked company profile), then invite people
python -m app.cli create-org --name "Company SARL" --plan compete --country SN --industry VA02.03.01 --capabilities solar_pumping,water_supply
python -m app.cli list-orgs
python -m app.cli invite --email owner@company.sn --org <org id from list-orgs> --role owner     # can save and start bids
python -m app.cli invite --email colleague@company.sn --org <org id> --role viewer              # read-only
```

Then sign in as the analyst and go to **Sources & runs**. Run the synthetic feed and publish the notice from the **Review queue**. Customers will see it under **Tenders**.

## Operating notes

- **Password reset (or lost phone):** `python -m app.cli reset-access --email E` prints a single-use link valid for 2 days. Add `--reset-mfa` if a staff member lost their authenticator. Using the link ends all existing sessions for that person. Self-service reset needs email delivery, which isn't built yet.
- **Lockout:** 5 wrong passwords lock an account for 15 minutes. Each IP address is also limited to 30 attempts per 10 minutes.
- **Sessions:** last 8 hours. Cookies are `HttpOnly`, `Secure` and `SameSite=Lax`. Writes sent with a cookie must come from the same origin.
- **Headers:** CSP, HSTS, `X-Frame-Options: DENY`, `nosniff`, and `no-store` on API responses.
- **Logs:** every sign-in, failed attempt, MFA event, invitation, data access and change is in the append-only `audit_events` table. Auditors can read it in the UI.
- **Rate limits** are in memory, so they hold per instance. Keep staging at **one instance** until they move to the database.

## Before inviting pilot customers (release gate)

`docs/UX_DESIGN_STANDARDS.md` §11 requires a weighted score of at least 90 (not provisional) and no critical defects. The last review scored **78, provisional**; see `reports/ux/`. Close these first, or record a written risk acceptance from the project owner:

- [ ] French labels for the VA taxonomy (UX-001)
- [ ] Screen-reader pass (NVDA or VoiceOver), 200% zoom, Safari, Firefox, Android Chrome
- [ ] French reviewed by a fluent speaker
- [ ] Hosting region and personal-data handling approved by counsel
- [ ] Identity approach accepted for the pilot (invite + password + staff TOTP), or a managed OIDC provider chosen
