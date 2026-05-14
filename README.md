# 📍 Volunite — Community Needs Intelligence Platform

> **Unite. Serve. Impact. Engineered for Precision.**

Volunite transforms scattered community data into actionable operational intelligence. Using Google's Gemini AI and Cloud Vision, it digitizes field surveys, performs geospatial clustering to identify crisis hotspots, and orchestrates optimal volunteer deployment. 

**This platform is engineered to meet the highest standards of professional UI/UX, designed for national-level hackathon excellence.**

🌐 **Live Dashboard**: [volunite.vercel.app](https://volunite.vercel.app)

---

## ✨ High-Fidelity UI/UX System

Volunite features a cohesive, premium design language built for clarity and impact across web and mobile.

- **Typography**: Powered by **Plus Jakarta Sans**, a modern geometric sans-serif that ensures readability and a premium, high-tech feel.
- **Glassmorphism**: Sophisticated translucent overlays and blur effects across the dashboard create depth and a modern "App-like" experience.
- **Dark-Mode Intelligence**: The central command map uses **CartoDB Dark Matter** tiles, providing superior visual contrast for critical need clusters.
- **Dynamic Feedback**: Real-time status indicators, shimmer loading states, and animated metric cards ensure a responsive, "alive" interface.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
│          Streamlit Dashboard  ·  Web PWA  ·  Flutter App        │
│          (Plus Jakarta Sans + Glassmorphism Design)             │
└─────────────────────────┬───────────────────────────────────────┘
                          │   REST API
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│  /surveys/*  │  /volunteers/*  │  /dashboard/*  │  /health      │
│  ML Pipeline │  Gemini Matcher │  OCR Processor │  Firebase     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Technical Highlights

- **Gemini AI Matching**: Intelligent volunteer-to-mission orchestration based on skills, proximity, and urgency.
- **K-Means Geospatial Clustering**: Automated identification of need density to optimize NGO resource allocation.
- **OCR Survey Digitization**: Cloud Vision API integration to bridge the gap between paper-based field work and digital intelligence.
- **CartoDB Visuals**: High-contrast dark mapping with custom categorical markers for instant situational awareness.

---

## ✅ Prerequisites

| Requirement | Details |
|---|---|
| **Python** | 3.11+ (FastAPI + ML) |
| **Flutter** | 3.x (Material 3 + Jakarta Sans) |
| **Node.js** | Vercel Deployment CLI |

> **💡 Zero-Config Demo:** Runs out-of-the-box with mock AI fallbacks and in-memory storage. No API keys required for initial testing.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Intelligence** | Google Gemini AI (Matching), scikit-learn (Clustering) |
| **Vision** | Google Cloud Vision (OCR Processor) |
| **Backend** | Python 3.11, FastAPI, Pydantic |
| **Mapping** | CartoDB Dark Matter, Leaflet, Folium |
| **Typography** | Plus Jakarta Sans (via Google Fonts) |
| **Mobile** | Flutter (Material 3, Provider, fl_chart) |
| **Deployment** | Vercel (Backend), Streamlit Cloud (Frontend) |

---

## 📂 Project Structure

```
Volunite/
├── backend/            # FastAPI Intelligence API + PWA Dashboard
├── frontend/           # Streamlit Coordinator Interface
├── mobile/             # Flutter Field Responder App
├── data/               # Sample Mission & Volunteer Datasets
└── vercel.json         # Production Deployment Configuration
```

---

## 🏆 Competition Entry

**Built for the Google Solution Challenge 2026 — Build with AI.**

**GitHub**: [github.com/00Aryan22/Volunite](https://github.com/00Aryan22/Volunite)

---

## 📄 License

MIT License. Designed with ❤️ for social impact.
