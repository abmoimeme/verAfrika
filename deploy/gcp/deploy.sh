#!/usr/bin/env bash
# Deploy VeraAfrika pilot staging to the Firebase project's Google Cloud:
#   Cloud Build → Artifact Registry → Cloud Run (europe-west1) + Cloud SQL PostgreSQL 16, fronted by Firebase Hosting.
#
# Run from the repository root in Google Cloud Shell:
#   bash deploy/gcp/deploy.sh            # asks for confirmation before creating billable resources
#   bash deploy/gcp/deploy.sh --yes      # non-interactive
#
# Safe to re-run: existing resources are reused; only a new image is built and rolled out.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-verafrika}"
REGION="${REGION:-europe-west1}"
SERVICE="verafrika-staging"
SQL_INSTANCE="verafrika-pg"
DB_NAME="verafrika"
DB_USER="verafrika"
AR_REPO="verafrika"
SECRET="verafrika-database-url"
RUN_SA_NAME="verafrika-run"
YES="${1:-}"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

[ -f Dockerfile ] && [ -f firebase.json ] || fail "Run this from the repository root (where Dockerfile and firebase.json are)."
command -v gcloud >/dev/null || fail "gcloud not found. Use Google Cloud Shell: https://shell.cloud.google.com"

gcloud config set project "$PROJECT_ID" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')" \
  || fail "Project '$PROJECT_ID' not found or no access. Set PROJECT_ID=<your Firebase project id> and retry."
TAG="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/app:$TAG"
CONN="$PROJECT_ID:$REGION:$SQL_INSTANCE"
RUN_SA="$RUN_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
PUBLIC_URL="https://$PROJECT_ID.web.app"

cat <<EOF

VeraAfrika pilot staging
  Project        $PROJECT_ID ($PROJECT_NUMBER)
  Region         $REGION
  Cloud Run      $SERVICE (max 1 instance, scales to zero)
  Cloud SQL      $SQL_INSTANCE — PostgreSQL 16, db-f1-micro, 10 GB, daily backups
  Public URL     $PUBLIC_URL (also https://$PROJECT_ID.firebaseapp.com)

This creates billable resources (the project must be on the Blaze plan).
Cloud SQL is charged while the instance exists, even when nobody uses the app.
EOF
if [ "$YES" != "--yes" ]; then
  read -r -p "Continue? Type 'deploy' to proceed: " answer
  [ "$answer" = "deploy" ] || fail "Cancelled."
fi

say "1/8 Enabling APIs"
gcloud services enable run.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com secretmanager.googleapis.com firebasehosting.googleapis.com iam.googleapis.com

say "2/8 Artifact Registry"
gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" >/dev/null 2>&1 || \
  gcloud artifacts repositories create "$AR_REPO" --repository-format=docker --location "$REGION" \
    --description="VeraAfrika container images"

say "3/8 Building image $IMAGE (Cloud Build)"
gcloud builds submit --tag "$IMAGE" .

say "4/8 Cloud SQL instance (first creation takes ~10 minutes)"
if ! gcloud sql instances describe "$SQL_INSTANCE" >/dev/null 2>&1; then
  gcloud sql instances create "$SQL_INSTANCE" --database-version=POSTGRES_16 --edition=ENTERPRISE \
    --tier=db-f1-micro --region="$REGION" --availability-type=zonal --storage-size=10 --storage-auto-increase \
    --backup-start-time=02:00 --enable-point-in-time-recovery --deletion-protection
fi
gcloud sql databases describe "$DB_NAME" --instance "$SQL_INSTANCE" >/dev/null 2>&1 || \
  gcloud sql databases create "$DB_NAME" --instance "$SQL_INSTANCE"

say "5/8 Database user and connection secret"
if ! gcloud secrets describe "$SECRET" >/dev/null 2>&1; then
  DB_PASS="$(openssl rand -hex 24)"
  if gcloud sql users list --instance "$SQL_INSTANCE" --format='value(name)' | grep -qx "$DB_USER"; then
    gcloud sql users set-password "$DB_USER" --instance "$SQL_INSTANCE" --password "$DB_PASS"
  else
    gcloud sql users create "$DB_USER" --instance "$SQL_INSTANCE" --password "$DB_PASS"
  fi
  printf 'postgresql://%s:%s@/%s?host=/cloudsql/%s' "$DB_USER" "$DB_PASS" "$DB_NAME" "$CONN" | \
    gcloud secrets create "$SECRET" --replication-policy=user-managed --locations="$REGION" --data-file=-
  unset DB_PASS
else
  echo "Secret $SECRET exists; keeping the current database password."
fi

say "6/8 Service account and permissions"
gcloud iam service-accounts describe "$RUN_SA" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$RUN_SA_NAME" --display-name="VeraAfrika Cloud Run"
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$RUN_SA" \
  --role=roles/cloudsql.client --condition=None >/dev/null
gcloud secrets add-iam-policy-binding "$SECRET" --member="serviceAccount:$RUN_SA" \
  --role=roles/secretmanager.secretAccessor >/dev/null

say "7/8 Deploying Cloud Run service $SERVICE"
# '@' is used as the env-var delimiter because VERAFRIKA_ALLOWED_HOSTS contains a comma.
gcloud run deploy "$SERVICE" --image "$IMAGE" --region "$REGION" --service-account "$RUN_SA" \
  --add-cloudsql-instances "$CONN" --set-secrets "DATABASE_URL=$SECRET:latest" \
  --set-env-vars "^@^VERAFRIKA_ENV=staging@VERAFRIKA_AUTO_MIGRATE=1@VERAFRIKA_TRUST_PROXY=1@PUBLIC_BASE_URL=$PUBLIC_URL@VERAFRIKA_ALLOWED_HOSTS=$PROJECT_ID.web.app,$PROJECT_ID.firebaseapp.com" \
  --min-instances 0 --max-instances 1 --cpu 1 --memory 512Mi --concurrency 40 --timeout 60 \
  --allow-unauthenticated
RUN_URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
for i in 1 2 3 4 5 6; do
  if curl -fsS "$RUN_URL/health"; then echo; break; fi
  [ "$i" = 6 ] && fail "Health check failed. Logs: gcloud run services logs read $SERVICE --region $REGION --limit 50"
  sleep 10
done

say "8/8 Firebase Hosting"
FIREBASE="firebase"; command -v firebase >/dev/null || FIREBASE="npx --yes firebase-tools@latest"
if ! $FIREBASE deploy --only hosting --project "$PROJECT_ID" --non-interactive; then
  cat <<EOF

Firebase Hosting was not deployed (usually: the Firebase CLI isn't signed in yet). Run:
  $FIREBASE login --no-localhost
  $FIREBASE deploy --only hosting --project $PROJECT_ID
EOF
  exit 1
fi
curl -fsS "$PUBLIC_URL/health" && echo

cat <<EOF

Done. VeraAfrika pilot staging is live at $PUBLIC_URL

Next: create your own analyst account (prints a single-use link):
  bash deploy/gcp/cli.sh invite --email you@example.com --org org_va_ops --role analyst
EOF
