GCLOUD deployment guide (Cloud Run)

This repo contains a Telethon-based long-running client. The recommended way to host it on Google Cloud is Cloud Run with CPU always allocated (instance-based billing) and one kept-warm instance. No personal secrets are included below; use placeholders and set env vars in Cloud Run.

Prereqs
- Install Google Cloud SDK and login: `gcloud auth login`
- Select your project: `gcloud config set project YOUR_PROJECT_ID`
- Have your Telegram creds ready (phone, api_id, api_hash). Do NOT commit them.

Enable APIs
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

Artifact Registry repo (one-time)
```bash
REGION=us-central1
REPO=ttt-repo
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Repo for ttt bot" || true
```

Build & push image
This repo ships `.gcloudignore` to keep the build context minimal.
```bash
REGION=us-central1
PROJECT_ID=YOUR_PROJECT_ID
IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/ttt-repo/ttt-bot:latest"

# From repo root
gcloud builds submit --tag "$IMAGE_URL" .
```

Session storage in Cloud Storage (one-time)
The Telethon session file is stored in a GCS bucket and mounted into Cloud Run as a volume.
```bash
REGION=us-central1
PROJECT_ID=YOUR_PROJECT_ID
SESSION_BUCKET="$PROJECT_ID-ttt-sessions"

# Create bucket (if not exists)
gsutil mb -l "$REGION" gs://"$SESSION_BUCKET" || true

# Upload your local Telethon session file (created after first local login)
# Do NOT commit it to git.
# Replace with your actual session filename if different
gsutil cp ./anon.session gs://"$SESSION_BUCKET"/anon.session

# Grant Cloud Run's default compute SA access to the bucket objects (optional if you see permission errors)
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='get(projectNumber)')
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gsutil iam ch serviceAccount:${SA}:roles/storage.objectAdmin gs://"$SESSION_BUCKET"
```

Deploy to Cloud Run (always-on CPU)
This mode allocates CPU continuously and is reliable for a background listener.
```bash
REGION=us-central1
PROJECT_ID=YOUR_PROJECT_ID
IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/ttt-repo/ttt-bot:latest"
SERVICE=ttt-bot
SESSION_BUCKET="$PROJECT_ID-ttt-sessions"

# Replace TELEGRAM_* with your own values
BOT_ARGS="--listen-all --profile dialogue"

gcloud run deploy "$SERVICE" \
  --image "$IMAGE_URL" \
  --region "$REGION" \
  --platform managed \
  --cpu 1 \
  --memory 512Mi \
  --no-cpu-throttling \
  --min-instances 1 \
  --ingress internal \
  --add-volume name=sessions,type=cloud-storage,bucket="$SESSION_BUCKET" \
  --add-volume-mount volume=sessions,mount-path=/sessions \
  --set-env-vars BOT_ARGS="$BOT_ARGS" \
  --set-env-vars TELEGRAM_PHONE_NUMBER="+YOUR_PHONE" \
  --set-env-vars TELEGRAM_API_ID="YOUR_API_ID" \
  --set-env-vars TELEGRAM_API_HASH="YOUR_API_HASH"

# Remove public access (defense-in-depth)
gcloud run services remove-iam-policy-binding "$SERVICE" \
  --region "$REGION" \
  --member=allUsers \
  --role=roles/run.invoker || true
```

Logs
```bash
# Show recent logs (preferred)
gcloud beta run services logs read ttt-bot --region us-central1 --limit=200

# Tail logs (alt)
gcloud beta run services logs tail ttt-bot --region us-central1

# Or via Cloud Logging filter
gcloud beta logging tail 'resource.type="cloud_run_revision" AND resource.labels.service_name="ttt-bot"'
```

Updating env vars / args later
```bash
gcloud run services update ttt-bot \
  --region us-central1 \
  --update-env-vars BOT_ARGS="--listen-all --profile dialogue" \
  --update-env-vars TELEGRAM_PHONE_NUMBER="+YOUR_PHONE",TELEGRAM_API_ID="YOUR_API_ID",TELEGRAM_API_HASH="YOUR_API_HASH"
```

Cleanup old images (optional)
```bash
# List digests
gcloud artifacts docker images list "$REGION-docker.pkg.dev/$PROJECT_ID/ttt-repo/ttt-bot" --format='value(version)'
# Delete by digest
gcloud artifacts docker images delete "$REGION-docker.pkg.dev/$PROJECT_ID/ttt-repo/ttt-bot@sha256:..." --delete-tags --quiet
```

Cost notes
- Always-on CPU (1 vCPU, 512 MiB, 1 min instance) ≈ $49/mo in Tier 1 regions; see Cloud Run pricing guides.
- If you need to reduce cost and accept reliability trade-offs, you can switch to CPU throttling and lower resources, but background listening may be unreliable.

Alternative (request-based CPU, not recommended for Telethon)
```bash
# CPU only during requests (less reliable for background listening)
gcloud run services update ttt-bot \
  --region us-central1 \
  --cpu-throttling \
  --cpu 0.5 \
  --memory 128Mi \
  --concurrency 1 \
  --execution-environment gen1
```

Security & repo hygiene
- Secrets are never committed. They are passed via env vars at deploy/update time.
- `.dockerignore` and `.gcloudignore` keep private files out of the image and build context.
- The service runs with `ingress=internal` and a minimal health HTTP server; no public endpoints are exposed.

