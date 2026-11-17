#!/usr/bin/env bash
# Run a VeraAfrika operations command (python -m app.cli ...) against the deployed staging database,
# as a one-off Cloud Run job, and print its output.
#
#   bash deploy/gcp/cli.sh list-orgs
#   bash deploy/gcp/cli.sh invite --email you@example.com --org org_va_ops --role analyst
#   bash deploy/gcp/cli.sh create-org --name "Company SARL" --plan compete --industry VA02.03.01 --capabilities solar_pumping,water_supply
#   bash deploy/gcp/cli.sh reset-access --email someone@example.com --reset-mfa
#
# Note: invitation and reset links appear in this output and in Cloud Logging for the job. They are single-use
# and expire (7 days for invitations, 2 days for resets).
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-verafrika}"
REGION="${REGION:-europe-west1}"
SERVICE="verafrika-staging"
JOB="verafrika-cli"
CONN="$PROJECT_ID:$REGION:verafrika-pg"
RUN_SA="verafrika-run@$PROJECT_ID.iam.gserviceaccount.com"

[ "$#" -ge 1 ] || { sed -n '2,12p' "$0"; exit 1; }
for a in "$@"; do case "$a" in *"|"*) echo "Arguments may not contain '|'." >&2; exit 1;; esac; done

gcloud config set project "$PROJECT_ID" >/dev/null
IMAGE="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(spec.template.spec.containers[0].image)')"
[ -n "$IMAGE" ] || { echo "Service $SERVICE not found. Run deploy/gcp/deploy.sh first." >&2; exit 1; }

# Keep the job on the same image as the live service.
gcloud run jobs deploy "$JOB" --image "$IMAGE" --region "$REGION" --service-account "$RUN_SA" \
  --set-cloudsql-instances "$CONN" --set-secrets "DATABASE_URL=verafrika-database-url:latest" \
  --set-env-vars "VERAFRIKA_ENV=staging,PUBLIC_BASE_URL=https://$PROJECT_ID.web.app" \
  --command python --args="-m,app.cli,list-orgs" --max-retries 0 --task-timeout 300 --quiet >/dev/null

# '|' delimiter so values with commas (e.g. --capabilities a,b) stay intact.
ARGS="^|^-m|app.cli"
for a in "$@"; do ARGS="$ARGS|$a"; done
EXECUTION="$(gcloud run jobs execute "$JOB" --region "$REGION" --args "$ARGS" --wait --format='value(metadata.name)')"

FILTER="resource.type=\"cloud_run_job\" AND resource.labels.job_name=\"$JOB\" AND labels.\"run.googleapis.com/execution_name\"=\"$EXECUTION\""
for _ in 1 2 3 4 5 6; do
  OUT="$(gcloud logging read "$FILTER" --order=asc --format='value(textPayload)' --freshness=1h)"
  [ -n "$OUT" ] && { printf '%s\n' "$OUT"; exit 0; }
  sleep 5
done
echo "Job $EXECUTION finished, but its output isn't in Cloud Logging yet. Retry in a minute:" >&2
echo "  gcloud logging read '$FILTER' --format='value(textPayload)'" >&2
