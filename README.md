# 📍 Volunite — Community Needs Intelligence Platform

> **Unite. Serve. Impact.**

Volunite helps Indian NGOs turn scattered community survey data — including paper surveys — into an intelligent, real-time map of urgent local needs. It automatically matches available volunteers to the tasks where they are needed most, using Google's Gemini AI. The platform features OCR-powered paper survey digitisation via Cloud Vision API, K-Means geographic clustering to identify need hotspots, and a beautiful real-time dashboard for NGO coordinators.

Built as a production-ready solution for the **Google Solution Challenge 2026 — Build with AI**.

🌐 **Live Demo**: [volunite.vercel.app](https://volunite.vercel.app)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
│          Streamlit Dashboard  ·  Web PWA  ·  Flutter App        │
└─────────────────────────┬───────────────────────────────────────┘
                          │   REST API
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│  /surveys/*  │  /volunteers/*  │  /dashboard/*  │  /health      │
│  ML Pipeline │  Gemini Matcher │  OCR Processor │  Firebase     │
└─────────────────────────────────────────────────────────────────┘

Deployment:
  Backend  →  Vercel (Free, Permanent) / Google Cloud Run
  Frontend →  Streamlit Community Cloud (Free)
  Mobile   →  Flutter (Android / iOS)
  Database →  Firebase Firestore (optional; in-memory demo without credentials)
  Map      →  OpenStreetMap + Leaflet (Free, no API key needed)
```

---

## ✅ Prerequisites

| Requirement | Details |
|---|---|
| **Python** | 3.11 or higher |
| **Node.js** | For Vercel CLI |
| **Flutter** | 3.x SDK |
| **Vercel Account** | Free at vercel.com |

> **💡 Demo Mode:** Works without ANY API keys! Uses mock AI responses and in-memory storage.

---

## 🚀 Quick Start (Local)

### 1. Clone the repository
```bash
git clone https://github.com/00Aryan22/Volunite.git
cd Volunite
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env — or leave defaults for demo mode (no keys needed)
```

### 3. Install & run backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Run Streamlit frontend (new terminal)
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

### 5. Open the dashboard
- **Web Dashboard**: http://localhost:8000
- **Streamlit UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

Demo credentials: `admin@volunite.app` / `admin123`

### 6. Flutter mobile (optional)
```bash
cd mobile
flutter pub get
flutter run
```

---

## 🌐 Vercel Deployment (Free & Permanent)

### One-command deploy:
```bash
npm i -g vercel
cd backend
vercel --prod
```

That's it! Vercel auto-detects the FastAPI Python app from `vercel.json`.

### Environment Variables on Vercel:
Set these in your Vercel project dashboard → Settings → Environment Variables:
```
GEMINI_API_KEY=your_key
CLOUD_VISION_API_KEY=your_key
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
ENABLE_DEMO_AUTH=true
```

---

## 🔑 API Keys (All Optional for Demo)

| Key | Where to Get | Required? |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) | Optional (mock fallback) |
| `CLOUD_VISION_API_KEY` | GCP Console → APIs | Optional (mock OCR) |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase Console → Service Accounts | Optional (in-memory) |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web Dashboard (PWA) |
| `GET` | `/health` | Health check |
| `POST` | `/auth/login` | Demo login |
| `POST` | `/surveys/submit` | Submit community need survey |
| `POST` | `/surveys/upload-csv` | Upload CSV with multiple surveys |
| `POST` | `/surveys/ocr` | Extract survey from image (OCR) |
| `GET` | `/surveys/all` | Get all surveys |
| `GET` | `/surveys/clusters` | K-Means clustered needs |
| `GET` | `/surveys/urgent` | Top 10 urgent needs |
| `POST` | `/volunteers/register` | Register volunteer |
| `GET` | `/volunteers/available` | Get available volunteers |
| `POST` | `/volunteers/match` | Run AI matching |
| `GET` | `/dashboard/stats` | Dashboard statistics |

**Interactive API Docs**: `https://your-app.vercel.app/docs`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11 + FastAPI |
| ML Pipeline | scikit-learn, Pandas, NumPy |
| AI Matching | Google Gemini API |
| OCR | Google Cloud Vision API |
| Database | Firebase Firestore (or in-memory) |
| Map | OpenStreetMap + Leaflet (free!) |
| Frontend | Streamlit + Folium |
| Mobile | Flutter (Android/iOS) |
| Deployment | **Vercel** (backend) + Streamlit Cloud (frontend) |

---

## 📂 Project Structure

```
Volunite/
├── backend/
│   ├── main.py              # FastAPI — all endpoints + web dashboard
│   ├── firebase_client.py   # Firestore helpers + in-memory fallback
│   ├── gemini_matcher.py    # Gemini AI volunteer matching
│   ├── ml_pipeline.py       # Urgency scoring + K-Means clustering
│   ├── ocr_processor.py     # Cloud Vision OCR
│   ├── models.py            # Pydantic models
│   ├── vercel.json          # Vercel deployment config
│   └── Dockerfile           # Cloud Run (alternative)
├── frontend/
│   ├── app.py               # Streamlit dashboard
│   └── map_component.py     # Folium OSM map helper
├── mobile/                  # Flutter field app
├── .github/workflows/       # CI/CD
├── data/sample_surveys.json # Sample data
├── vercel.json              # Root Vercel config
└── README.md
```

---

## 🏆 Built for

**Google Solution Challenge 2026 — Build with AI** 🚀

**GitHub**: [github.com/00Aryan22/Volunite](https://github.com/00Aryan22/Volunite)

---

## 📄 License

MIT License.
