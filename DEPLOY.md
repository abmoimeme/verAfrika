# Deploying VeraAfrika pilot staging

Staging runs one container: the API and pilot UI together, plus a managed PostgreSQL database. Sign-in works by invitation only. VeraAfrika staff must use an authenticator app (TOTP); pilot customers sign in with email and password. The development profile picker, sample personas and API docs are all disabled outside development.

> **Data notice.** The tender in staging is synthetic test data. Accounts are real: names and emails of pilot users are personal data. The hosting region is still an open decision (LLD §10.1, `HOSTING_REGION`). The Firebase deployment uses `europe-west1` (Belgium) until counsel confirms the Senegal CDP / transfer position.

## Option A — Firebase project `verafrika` (Google Cloud, europe-west1) — chosen

Architecture: **Firebase Hosting** (`https://verafrika.web.app`) → **Cloud Run** service `verafrika-staging` → **Cloud SQL for PostgreSQL 16** (`verafrika-pg`). Everything is in `europe-west1`, the region of the existing Realtime Database. The database password lives only in **Secret Manager**. The Realtime Database is **not** used.

**Prerequisites**
- The project is on the **Blaze** (pay-as-you-go) plan. Cloud SQL and Cloud Run need billing, and Cloud SQL is charged for as long as the instance exists.
- Firebase Hosting is enabled for the project. If the console shows "Get started" under Hosting, click it once.

**Deploy (about 15 minutes the first time)**
1. Open **Google Cloud Shell** (shell.cloud.google.com) signed in as the project owner, then:
   ```bash
   git clone https://github.com/abmoimeme/verafrika && cd verafrika
   bash deploy/gcp/deploy.sh
   ```
2. The script shows what it will create and waits until you type `deploy`. It then:
   1. Enables the APIs.
   2. Builds the image with Cloud Build.
   3. Creates Cloud SQL (PostgreSQL 16, db-f1-micro, daily backups, point-in-time recovery, deletion protection).
   4. Stores the connection string in Secret Manager.
   5. Creates a dedicated service account with only Cloud SQL Client and Secret Accessor.
   6. Deploys Cloud Run (maximum 1 instance, scales to zero) and checks `/health`.
   7. Deploys Firebase Hosting.
3. If the Firebase CLI asks you to sign in, run the two commands it prints (`firebase login --no-localhost`, then the deploy).
4. Re-running the script is safe. It reuses existing resources, builds a new image from the current commit and rolls it out.

**Why two settings exist:**
- **Session cookie name:** Firebase Hosting passes only the cookie named `__session` to Cloud Run, so the app uses that name.
- **`VERAFRIKA_ALLOWED_HOSTS`:** requests reach Cloud Run under its `run.app` address, so the cross-site check is told that `verafrika.web.app` and `verafrika.firebaseapp.com` are the legitimate front ends.

## Option B — Render

`render.yaml` remains in the repo as an alternative: **New → Blueprint** in Render, set `PUBLIC_BASE_URL`, deploy.

## Onboarding people

On Google Cloud, `bash deploy/gcp/cli.sh <command>` runs any of the commands below as a one-off Cloud Run job against the staging database and prints the result. For example: `bash deploy/gcp/cli.sh invite --email you@example.com --org org_va_ops --role analyst`. On Render, run them in the service's Shell as `python -m app.cli <command>`. Each invitation link is single-use and valid for 7 days, and links also appear in the job's Cloud Logging entry. Send each link to the person yourself; email delivery isn't built yet.

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
- **Rate limits** are in memory, so they hold per instance. The deploy script caps Cloud Run at **one instance** until they move to the database. Per-account lockout doesn't depend on the client IP; the per-IP limit relies on the forwarded address, which a determined client can vary.

## Before inviting pilot customers (release gate)

`docs/UX_DESIGN_STANDARDS.md` §11 requires a weighted score of at least 90 (not provisional) and no critical defects. The last review scored **78, provisional**; see `reports/ux/`. Close these first, or record a written risk acceptance from the project owner:

- [ ] French labels for the VA taxonomy (UX-001)
- [ ] Screen-reader pass (NVDA or VoiceOver), 200% zoom, Safari, Firefox, Android Chrome
- [ ] French reviewed by a fluent speaker
- [ ] Hosting region and personal-data handling approved by counsel
- [ ] Identity approach accepted for the pilot (invite + password + staff TOTP), or a managed OIDC provider chosen
