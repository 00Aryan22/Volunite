# Deployment guide

## Prerequisites

- Google Cloud project with billing, APIs enabled (Vision, Maps as needed), `gcloud` CLI authenticated.
- Firebase project (optional for hosted Streamlit + static assets).
- Docker (for Cloud Run image build).

## Backend (Cloud Run)

From the **repository root** (not `backend/`):

```bash
docker build -f backend/Dockerfile -t gcr.io/$PROJECT_ID/volunteermap-backend:latest .
docker push gcr.io/$PROJECT_ID/volunteermap-backend:latest
gcloud run deploy volunteermap-backend \
  --image gcr.io/$PROJECT_ID/volunteermap-backend:latest \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8080
```

Set environment variables in the Cloud Run console (recommended: **Secret Manager**) for:

- `GEMINI_API_KEY`, `CLOUD_VISION_API_KEY`
- `FIREBASE_SERVICE_ACCOUNT_PATH` or mount secret as file, **or** `FIREBASE_SERVICE_ACCOUNT_JSON` if you accept the operational risk
- `ENABLE_DEMO_AUTH=false`
- `CORS_ORIGINS` — comma-separated list of allowed web origins (e.g. your Streamlit Cloud URL)

## Streamlit dashboard

1. Set `BACKEND_URL` to your Cloud Run URL.
2. Deploy via Streamlit Community Cloud or your own host; ensure outbound network access to the API.

## Flutter mobile

Build with your API host:

```bash
cd mobile
flutter build apk --dart-define=API_BASE_URL=https://your-api.run.app
```

## Scripted deploy

See `deploy.sh` for an opinionated Cloud Run + Firebase Hosting flow. Review and adapt `gcloud run deploy` env injection for production (prefer secrets over raw `.env` greps).
