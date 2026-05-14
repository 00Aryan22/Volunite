# VolunteerMap architecture

## Components

| Layer | Stack | Role |
|--------|--------|------|
| Web dashboard | Streamlit (`frontend/app.py`) | NGO coordinator UI: metrics, Folium map, survey/OCR/matching flows |
| Optional HTML prototype | FastAPI `GET /` (`backend/main.py`) | Self-contained Tailwind + Leaflet demo shell |
| Mobile app | Flutter (`mobile/`) | Field officers: surveys, map, OCR, matching (HTTP client) |
| API | FastAPI + Uvicorn (`backend/main.py`) | REST: surveys, volunteers, clusters, OCR, Gemini matching, stats |
| Data | Firestore (optional) or in-process memory | Persistence; demo mode when credentials are absent |
| ML | scikit-learn + pandas (`ml_pipeline.py`) | Urgency score + geographic K-Means clusters |
| AI | Gemini (`gemini_matcher.py`), Vision (`ocr_processor.py`) | Matching + paper survey OCR; mock fallbacks without keys |

## Request flow (Streamlit)

1. Streamlit server calls FastAPI using `BACKEND_URL` (server-side `requests`, no browser CORS for that path).
2. Browser-only clients (hosted HTML on another origin, or future SPA) require `CORS_ORIGINS` to include their origin.

## Security model (summary)

- **Production**: disable demo login (`ENABLE_DEMO_AUTH=false`), restrict `CORS_ORIGINS`, store Firebase JSON as a file path or Secret Manager, never commit `.env`.
- **Firestore rules** (`firebase/firestore.rules`) apply to client SDK access; the Python backend uses the Admin SDK and bypasses these rules for server writes.

## Deployment artifacts

- **Cloud Run**: build Docker image from **repository root** with `docker build -f backend/Dockerfile .` so `data/sample_surveys.json` is included.
- **Streamlit / Firebase Hosting**: configure `BACKEND_URL` to the deployed API URL.
