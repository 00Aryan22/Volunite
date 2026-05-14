"""
Volunite — FastAPI Backend Application.

Main API server providing endpoints for survey management, volunteer
registration, AI-powered matching, OCR processing, and dashboard analytics.

Built for Google Solution Challenge 2026 — Build with AI.
"""

import os
import io
import csv
import json
import logging
from typing import List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

from models import (
    SurveySubmit, Survey, VolunteerRegister, Volunteer,
    MatchResult, ClusterResult, DashboardStats, HealthResponse,
    LoginCredentials,
)
from firebase_client import (
    save_survey, get_all_surveys, save_volunteer,
    get_available_volunteers, save_match_result, load_sample_data,
    delete_volunteer,
)
from ml_pipeline import compute_urgency_score, cluster_needs
from gemini_matcher import match_volunteers
from ocr_processor import extract_survey_from_image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Upload limits (bytes)
_MAX_UPLOAD_MB = float(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = int(_MAX_UPLOAD_MB * 1024 * 1024)


def _parse_cors_origins() -> tuple[list[str], bool]:
    """
    Return (origins, allow_credentials).

    Browsers reject allow_origins=['*'] together with allow_credentials=True.
    Default dev origins include Streamlit and local dashboards.
    """
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw == "*":
        return ["*"], False
    if raw:
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        return origins, True
    return [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ], True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler: load sample data on startup."""
    # Try multiple paths (works on both local dev and Vercel)
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sample_surveys.json"),
        os.path.join(os.path.dirname(__file__), "..", "data", "sample_surveys.json"),
        os.path.join(os.getcwd(), "data", "sample_surveys.json"),
        "/var/task/data/sample_surveys.json",  # Vercel serverless path
    ]
    loaded = False
    for sample_path in possible_paths:
        if os.path.exists(sample_path):
            load_sample_data(sample_path)
            logger.info(f"Sample data loaded from: {sample_path}")
            loaded = True
            break
    if not loaded:
        # Load embedded sample data as fallback
        from firebase_client import load_embedded_sample_data
        load_embedded_sample_data()
        logger.info("Loaded embedded sample data (Vercel fallback).")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title="Volunite API",
    description="Volunite — Community Needs Intelligence Platform. Unite. Serve. Impact.",
    version="2.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    return response


_cors_origins, _cors_credentials = _parse_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ─── Root & Health Check ─────────────────────────────────────────────────────


# ─── Auth & Session Management ───────────────────────────────────────────────

DEMO_ACCOUNTS = {
    "admin@volunite.app": {"pass": "admin123", "role": "admin", "name": "System Admin"},
    "sangli_lead@volunite.app": {"pass": "sangli123", "role": "lead", "name": "Sangli Coordinator"},
    "pune_lead@volunite.app": {"pass": "pune123", "role": "lead", "name": "Pune Coordinator"},
    "+919999999999": {"pass": "123456", "role": "field", "name": "Field Officer"},
    "google_demo": {"pass": "google", "role": "admin", "name": "Google User (Demo)"},
}


def _demo_auth_enabled() -> bool:
    return os.getenv("ENABLE_DEMO_AUTH", "true").lower() in ("1", "true", "yes")


@app.post("/auth/login", tags=["Auth"])
async def login(credentials: LoginCredentials):
    """
    Validate credentials and return user profile.
    Supports email, phone (+91...), or google_demo.

    Set ENABLE_DEMO_AUTH=false in production and use Firebase Auth / your IdP instead.
    """
    if not _demo_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo authentication is disabled. Configure your identity provider.",
        )

    identity = credentials.identity.strip()
    password = credentials.password

    if identity in DEMO_ACCOUNTS and DEMO_ACCOUNTS[identity]["pass"] == password:
        user = DEMO_ACCOUNTS[identity].copy()
        user.pop("pass")
        user["token"] = f"demo_token_{identity}"
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials.",
    )


@app.delete("/volunteers/{volunteer_id}", tags=["Volunteers"])
async def remove_volunteer(volunteer_id: str):
    """Remove a volunteer profile from the database."""
    try:
        delete_volunteer(volunteer_id)
        return {"message": "Volunteer removed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove volunteer: {str(e)}",
        )


@app.get("/", tags=["System"], response_class=HTMLResponse)
async def root():
    """Interactive Web Dashboard - Volunite Community Intelligence Platform."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Volunite | Unite. Serve. Impact.</title>
<meta name="description" content="Volunite — AI-powered community needs intelligence platform connecting volunteers to where they're needed most.">
<meta name="theme-color" content="#00BFA5">
<link rel="manifest" href="/manifest.json">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root {
        --primary: #00BFA5;
        --secondary: #006064;
        --accent: #f43f5e;
        --bg-deep: #020617;
        --glass-bg: rgba(15, 23, 42, 0.6);
        --glass-border: rgba(255, 255, 255, 0.08);
    }
    body { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        background: radial-gradient(circle at 0% 0%, #0f172a 0%, #020617 100%);
        color: #f1f5f9; 
        min-height: 100vh;
        overflow-x: hidden;
    }
    .glass { 
        background: var(--glass-bg); 
        backdrop-filter: blur(16px); 
        border: 1px solid var(--glass-border); 
        box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5); 
    }
    .sidebar-gradient { 
        background: rgba(2, 6, 23, 0.8); 
        backdrop-filter: blur(24px); 
        border-right: 1px solid var(--glass-border); 
    }
    .nav-item { 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        cursor: pointer; 
        border-radius: 16px; 
        color: #94a3b8; 
    }
    .nav-item:hover { 
        background: rgba(0, 191, 165, 0.1); 
        color: var(--primary);
        padding-left: 1.5rem;
    }
    .nav-item.active { 
        background: linear-gradient(90deg, rgba(0, 191, 165, 0.15) 0%, transparent 100%); 
        color: var(--primary); 
        border-left: 3px solid var(--primary);
        border-radius: 0 16px 16px 0;
    }
    .tab-content { display: none; opacity: 0; transform: translateY(20px); transition: all 0.5s ease-out; }
    .tab-content.active { display: block; opacity: 1; transform: translateY(0); }
    #map { 
        height: 480px; 
        border-radius: 32px; 
        z-index: 10; 
        border: 1px solid var(--glass-border); 
        box-shadow: 0 20px 50px -15px rgba(0, 0, 0, 0.7);
    }
    .leaflet-container { background: var(--bg-deep) !important; }
    #login-overlay { 
        position: fixed; inset: 0; z-index: 9999; 
        background: var(--bg-deep);
        display: flex; align-items: center; justify-content: center; 
    }
    .btn-premium { 
        background: linear-gradient(135deg, #00BFA5 0%, #00897B 100%); 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .btn-premium:hover { 
        transform: translateY(-4px) scale(1.02); 
        box-shadow: 0 15px 30px -10px rgba(0, 191, 165, 0.5); 
    }
    .skeleton {
        background: linear-gradient(90deg, #0f172a 25%, #1e293b 50%, #0f172a 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite linear;
    }
    @keyframes loading {
        to { background-position: -200% 0; }
    }
    .pulse-glow {
        animation: pulse-glow 2s infinite ease-in-out;
    }
    @keyframes pulse-glow {
        0%, 100% { opacity: 0.5; filter: blur(2px); }
        50% { opacity: 1; filter: blur(0px); }
    }
</style>
</head>
<body class="antialiased text-slate-200">
    <!-- Login Overlay -->
    <div id="login-overlay">
        <div class="glass p-12 rounded-[48px] w-full max-w-md space-y-10 text-center border-teal-500/10">
            <div class="space-y-4">
                <div class="w-24 h-24 rounded-[32px] flex items-center justify-center mx-auto shadow-[0_20px_50px_rgba(0,191,165,0.3)]" style="background: linear-gradient(135deg, #00BFA5, #006064);">
                    <i class="fa-solid fa-map-pin text-5xl text-white"></i>
                </div>
                <div>
                    <h2 class="text-4xl font-extrabold text-white tracking-tighter">Volunite</h2>
                    <p class="text-[10px] font-black uppercase tracking-[0.4em] text-teal-400 mt-2">Unite. Serve. Impact.</p>
                </div>
            </div>
            
            <div class="space-y-4">
                <div class="space-y-3">
                    <input id="login-email" type="text" placeholder="Admin ID or Phone" class="w-full bg-slate-900/50 border border-slate-800 rounded-2xl p-5 text-sm focus:border-teal-500 outline-none transition-all placeholder:text-slate-500 text-white font-medium">
                    <input id="login-pass" type="password" placeholder="Access Code" class="w-full bg-slate-900/50 border border-slate-800 rounded-2xl p-5 text-sm focus:border-teal-500 outline-none transition-all placeholder:text-slate-500 text-white font-medium">
                    <button onclick="handleEmailLogin()" class="w-full py-5 btn-premium text-white rounded-2xl font-bold text-sm uppercase tracking-[0.2em] mt-4 shadow-xl">Enter Volunite Portal</button>
                </div>
            </div>
            
            <div class="p-6 bg-slate-950/50 rounded-3xl border border-slate-800">
                <p class="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-2">Demo Auth</p>
                <code class="text-xs text-teal-400/90 font-bold">admin@volunite.app / admin123</code>
            </div>
        </div>
    </div>

    <!-- Main Dashboard -->
    <div id="main-dashboard" class="flex h-screen overflow-hidden hidden">
        <aside class="w-80 sidebar-gradient flex flex-col p-8 space-y-10">
            <div class="flex items-center gap-4 px-2">
                <div class="w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg" style="background: linear-gradient(135deg, #00BFA5, #006064);">
                    <i class="fa-solid fa-map-pin text-2xl text-white"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-black tracking-tighter text-white">Volunite</h1>
                    <p class="text-[9px] text-teal-500 font-black uppercase tracking-[0.3em]">AI Intelligence</p>
                </div>
            </div>

            <nav class="flex-1 space-y-3">
                <div onclick="switchTab('dashboard')" id="nav-dashboard" class="nav-item active flex items-center gap-4 px-5 py-4 text-sm font-bold">
                    <i class="fa-solid fa-grid-2 w-5"></i> Dashboard
                </div>
                <div onclick="switchTab('surveys')" id="nav-surveys" class="nav-item flex items-center gap-4 px-5 py-4 text-sm font-bold">
                    <i class="fa-solid fa-file-invoice w-5 text-amber-500"></i> Field Surveys
                </div>
                <div onclick="switchTab('volunteers')" id="nav-volunteers" class="nav-item flex items-center gap-4 px-5 py-4 text-sm font-bold">
                    <i class="fa-solid fa-users-medical w-5 text-blue-500"></i> Responders
                </div>
                <div onclick="switchTab('matching')" id="nav-matching" class="nav-item flex items-center gap-4 px-5 py-4 text-sm font-bold">
                    <i class="fa-solid fa-sparkles w-5 text-purple-500"></i> Smart Match
                </div>
            </nav>

            <div class="pt-8 border-t border-slate-800">
                <div onclick="logout()" class="flex items-center gap-4 px-5 py-4 text-sm font-bold text-slate-400 hover:text-rose-400 cursor-pointer transition-all">
                    <i class="fa-solid fa-arrow-right-from-bracket"></i> Sign Out
                </div>
            </div>
        </aside>

        <main class="flex-1 overflow-y-auto p-12 bg-transparent">
            <header class="flex justify-between items-center mb-12">
                <div>
                    <h2 id="page-title" class="text-4xl font-black text-white tracking-tighter flex items-center gap-3">
                        Dashboard
                    </h2>
                    <p id="page-subtitle" class="text-slate-300 text-sm mt-2 font-semibold">Real-time community needs intelligence</p>
                </div>
                <div class="flex items-center gap-5 glass px-8 py-4 rounded-3xl border-teal-500/10">
                    <div class="text-right">
                        <p id="user-name" class="text-sm font-extrabold text-white">--</p>
                        <p id="user-role" class="text-[10px] font-black text-teal-400 uppercase tracking-widest">--</p>
                    </div>
                    <div class="w-12 h-12 bg-slate-800 rounded-2xl flex items-center justify-center font-black text-teal-400 border border-slate-700 text-xl" id="user-initial">V</div>
                </div>
            </header>
            
            <!-- Dashboard Tab -->
            <div id="tab-dashboard" class="tab-content active space-y-12">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
                    <div class="glass p-8 rounded-[32px] group hover:border-teal-500/30 transition-all cursor-default">
                        <p class="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-2">Total Surveys</p>
                        <p class="text-5xl font-black text-white tracking-tighter" id="stat-total-surveys">--</p>
                    </div>
                    <div class="glass p-8 rounded-[32px] group hover:border-blue-500/30 transition-all cursor-default">
                        <p class="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-2">Active Volunteers</p>
                        <p class="text-5xl font-black text-white tracking-tighter" id="stat-active-volunteers">--</p>
                    </div>
                    <div class="glass p-8 rounded-[32px] group hover:border-rose-500/30 transition-all cursor-default">
                        <p class="text-[10px] text-rose-400 font-black uppercase tracking-widest mb-2">Urgent Needs</p>
                        <p class="text-5xl font-black text-rose-400 tracking-tighter" id="stat-urgent-needs">--</p>
                    </div>
                    <div class="glass p-8 rounded-[32px] group hover:border-purple-500/30 transition-all cursor-default">
                        <p class="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-2">Avg Urgency</p>
                        <p class="text-5xl font-black text-white tracking-tighter" id="stat-avg-urgency">--</p>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    <div class="lg:col-span-2 space-y-6">
                        <div class="flex justify-between items-center px-2">
                            <h3 class="text-2xl font-black text-white flex items-center gap-3">
                                <i class="fa-solid fa-map-location-dot text-teal-500"></i> Impact Hotspots
                            </h3>
                            <button onclick="updateMap()" class="text-xs font-black text-teal-400 uppercase tracking-widest hover:text-teal-300 flex items-center gap-2">
                                <i class="fa-solid fa-rotate"></i> Sync Live
                            </button>
                        </div>
                        <div id="map"></div>
                    </div>
                    <div class="space-y-6">
                        <h3 class="text-2xl font-black text-white flex items-center gap-3 px-2">
                            <i class="fa-solid fa-fire-flame-curved text-rose-500"></i> Priorities
                        </h3>
                        <div id="urgent-list" class="space-y-4">
                            <!-- Skeleton loaders would go here -->
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                    <div class="glass p-10 rounded-[40px]">
                        <h3 class="text-xl font-black mb-8 text-white flex items-center gap-3">
                            <i class="fa-solid fa-chart-simple text-blue-500"></i> Category Breakdown
                        </h3>
                        <div class="h-64"><canvas id="categoryChart"></canvas></div>
                    </div>
                    <div class="glass p-10 rounded-[40px]">
                        <h3 class="text-xl font-black mb-8 text-white flex items-center gap-3">
                            <i class="fa-solid fa-clock-rotate-left text-amber-500"></i> Recent Activity
                        </h3>
                        <div id="activity-list" class="space-y-5">
                             <!-- Activity items -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Surveys Tab -->
            <div id="tab-surveys" class="tab-content">
                <div class="glass rounded-[40px] overflow-hidden">
                    <table class="w-full text-left">
                        <thead class="bg-slate-900/80 border-b border-slate-800 text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                            <tr>
                                <th class="px-10 py-6">Geographic District</th>
                                <th class="px-8 py-6">Need Category</th>
                                <th class="px-8 py-6 text-center">Urgency</th>
                                <th class="px-8 py-6 text-right">People Affected</th>
                            </tr>
                        </thead>
                        <tbody id="surveys-table-body" class="text-sm font-semibold">
                            <!-- Rows -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Volunteers Tab -->
            <div id="tab-volunteers" class="tab-content">
                <div id="volunteers-grid" class="grid grid-cols-1 md:grid-cols-3 gap-8"></div>
            </div>

            <!-- AI Matching Tab -->
            <div id="tab-matching" class="tab-content space-y-10 pb-20">
                <div class="glass p-16 rounded-[48px] text-center space-y-8 border-teal-500/20 relative overflow-hidden">
                    <div class="absolute -top-24 -left-24 w-64 h-64 bg-teal-500/10 rounded-full blur-[80px]"></div>
                    <div class="absolute -bottom-24 -right-24 w-64 h-64 bg-blue-500/10 rounded-full blur-[80px]"></div>
                    
                    <div class="w-24 h-24 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-[32px] flex items-center justify-center mx-auto text-4xl shadow-2xl shadow-teal-500/30 relative">
                        <i class="fa-solid fa-wand-magic-sparkles"></i>
                    </div>
                    <div class="max-w-xl mx-auto space-y-3">
                        <h3 class="text-3xl font-black text-white tracking-tighter">Gemini Intelligence Matching</h3>
                        <p class="text-slate-300 font-semibold">Auto-assign the best volunteers to the most critical community needs based on location, skills, and urgency metrics.</p>
                    </div>
                    <button id="btn-run-match" onclick="runAIMatch()" class="bg-teal-500 text-white px-16 py-5 rounded-[20px] font-black text-sm uppercase tracking-widest hover:scale-105 transition-all shadow-[0_20px_40px_rgba(0,191,165,0.3)]">Optimize Operations</button>
                    
                    <div id="matching-loader" class="hidden flex flex-col items-center gap-4">
                        <div class="w-12 h-12 border-4 border-teal-500/30 border-t-teal-500 rounded-full animate-spin"></div>
                        <p class="text-teal-400 font-black text-[10px] tracking-[0.4em] uppercase pulse-glow">Analyzing Human Capital Data...</p>
                    </div>
                </div>
                <div id="matches-results" class="grid grid-cols-1 md:grid-cols-2 gap-8"></div>
            </div>
        </main>
    </div>

    <script>
        let map, chartInstance;
        let currentUser = null;

        async function handleEmailLogin() {
            const identity = document.getElementById('login-email').value;
            const password = document.getElementById('login-pass').value;
            performLogin(identity, password);
        }

        async function performLogin(identity, password) {
            if (identity === 'admin@volunteermap.org') identity = 'admin@volunite.app';
            try {
                const res = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ identity, password })
                });
                
                if (!res.ok) throw new Error('Unauthorized Access');
                
                const user = await res.json();
                currentUser = user;
                localStorage.setItem('vn_user_v2', JSON.stringify(user));
                document.getElementById('login-overlay').style.opacity = '0';
                setTimeout(() => {
                    document.getElementById('login-overlay').style.display = 'none';
                    document.getElementById('main-dashboard').style.display = 'flex';
                    initDashboard();
                }, 500);
            } catch (e) { 
                alert('Authentication Failed: ' + e.message); 
            }
        }

        function initDashboard() {
            document.getElementById('user-name').innerText = currentUser.name;
            document.getElementById('user-role').innerText = currentUser.role;
            document.getElementById('user-initial').innerText = currentUser.name[0];
            initMap();
            fetchData();
        }

        function logout() {
            localStorage.removeItem('vn_user_v2');
            window.location.reload();
        }

        function initMap() {
            if (map) return;
            map = L.map('map', { zoomControl: false, scrollWheelZoom: false }).setView([18.5204, 73.8567], 7);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; CartoDB | OpenStreetMap'
            }).addTo(map);
            L.control.zoom({ position: 'bottomright' }).addTo(map);
        }

        const COLORS = {
            healthcare: '#f43f5e', food: '#f59e0b',
            education: '#3b82f6', sanitation: '#10b981', employment: '#a855f7'
        };
        const ICONS = {
            healthcare: '🏥', food: '🍚', education: '📚', sanitation: '🚿', employment: '💼'
        };

        async function updateMap() {
            try {
                const res = await fetch('/surveys/clusters');
                const data = await res.json();
                map.eachLayer((layer) => { if (layer instanceof L.Marker || layer instanceof L.CircleMarker) map.removeLayer(layer); });
                
                (data.clusters || []).forEach(c => {
                    const color = COLORS[c.top_category] || '#00BFA5';
                    const icon = ICONS[c.top_category] || '📍';
                    const radius = Math.max(12, Math.min(c.count * 5, 40));
                    L.circleMarker([c.centroid.lat, c.centroid.lng], {
                        radius, fillColor: color, color: '#fff',
                        weight: 2.5, fillOpacity: 0.85
                    })
                    .addTo(map)
                    .bindPopup(`<div style="font-family:'Plus Jakarta Sans',sans-serif;min-width:180px;color:#0f172a;padding:5px">
                        <p style="margin:0;font-size:10px;font-weight:900;text-transform:uppercase;color:${color}">${icon} ${c.top_category}</p>
                        <h4 style="margin:4px 0;font-weight:800">Cluster #${c.cluster_id + 1}</h4>
                        <div style="display:flex;justify-content:space-between;font-size:11px;font-weight:600;border-top:1px solid #eee;margin-top:8px;padding-top:8px">
                            <span>NEEDS: <b>${c.count}</b></span>
                            <span>URGENCY: <b>${c.total_urgency.toFixed(1)}</b></span>
                        </div>
                    </div>`);
                });
            } catch(e) { console.warn('Map Error:', e); }
        }

        function switchTab(tabId) {
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(t => { t.classList.remove('active'); });
            
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            
            const activeTab = document.getElementById('tab-' + tabId);
            activeTab.style.display = 'block';
            setTimeout(() => { activeTab.classList.add('active'); }, 10);
            
            document.getElementById('nav-' + tabId).classList.add('active');
            
            const meta = {
                'dashboard': ['Dashboard', 'Intelligence for social impact'],
                'surveys': ['Field Surveys', 'Ground-level data collection'],
                'volunteers': ['Responders', 'Mobile workforce management'],
                'matching': ['Smart Match', 'Algorithmic task allocation']
            };
            
            document.getElementById('page-title').innerText = meta[tabId][0];
            document.getElementById('page-subtitle').innerText = meta[tabId][1];

            if (tabId === 'dashboard') { setTimeout(() => map.invalidateSize(), 100); fetchData(); }
            if (tabId === 'surveys') fetchSurveys();
            if (tabId === 'volunteers') fetchVolunteers();
        }

        async function fetchData() {
            const res = await fetch('/dashboard/stats');
            const data = await res.json();
            document.getElementById('stat-total-surveys').innerText = data.total_surveys;
            document.getElementById('stat-active-volunteers').innerText = data.active_volunteers;
            document.getElementById('stat-urgent-needs').innerText = data.urgent_needs;
            document.getElementById('stat-avg-urgency').innerText = data.avg_urgency.toFixed(1);
            updateChart(data.category_breakdown);
            updateMap();
            fetchUrgent();
        }

        function updateChart(data) {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            if (chartInstance) chartInstance.destroy();
            chartInstance = new Chart(ctx, { 
                type: 'bar', 
                data: { 
                    labels: Object.keys(data).map(k => k.toUpperCase()), 
                    datasets: [{ 
                        data: Object.values(data), 
                        backgroundColor: ['#f43f5e', '#f59e0b', '#3b82f6', '#10b981', '#a855f7'], 
                        borderRadius: 12,
                        barThickness: 35
                    }] 
                }, 
                options: { 
                    responsive: true, maintainAspectRatio: false, 
                    plugins: { legend: { display: false } }, 
                    scales: { 
                        y: { display: false }, 
                        x: { grid: { display: false }, ticks: { color: '#64748b', font: { weight: '800', size: 10 } } } 
                    } 
                } 
            });
        }

        async function fetchUrgent() {
            const res = await fetch('/surveys/urgent');
            const data = await res.json();
            const list = document.getElementById('urgent-list'); list.innerHTML = '';
            (data.urgent_needs || []).slice(0, 5).forEach(n => { 
                list.innerHTML += `<div class="glass p-6 rounded-3xl flex justify-between items-center border-l-4 border-rose-500 hover:scale-[1.02] transition-transform">
                    <div class="flex gap-4 items-center">
                        <div class="w-2.5 h-2.5 bg-rose-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.5)]"></div>
                        <div>
                            <p class="text-sm font-black text-white tracking-tight">${n.district}</p>
                            <p class="text-[9px] text-slate-500 font-black uppercase tracking-widest">${n.category}</p>
                        </div>
                    </div>
                    <p class="text-2xl font-black text-white">${n.urgency_score.toFixed(0)}</p>
                </div>`; 
            });
        }

        async function fetchSurveys() {
            const res = await fetch('/surveys/all');
            const data = await res.json();
            const body = document.getElementById('surveys-table-body'); body.innerHTML = '';
            (data.surveys || []).forEach(s => { 
                body.innerHTML += `<tr class="border-b border-slate-900/50 hover:bg-slate-900/30 transition-all group">
                    <td class="px-10 py-6 font-bold text-white group-hover:text-teal-400">${s.district}</td>
                    <td class="px-8 py-6 uppercase text-[10px] font-black text-slate-500 tracking-widest">${s.category}</td>
                    <td class="px-8 py-6 text-center font-mono font-black text-teal-400">${s.urgency_score.toFixed(1)}</td>
                    <td class="px-8 py-6 text-right text-slate-400 font-bold">${s.affected_count}</td>
                </tr>`; 
            });
        }

        async function fetchVolunteers() {
            const res = await fetch('/volunteers/available');
            const data = await res.json();
            const grid = document.getElementById('volunteers-grid'); grid.innerHTML = '';
            (data.volunteers || []).forEach(v => { 
                grid.innerHTML += `<div class="glass p-8 rounded-[40px] space-y-5 relative group hover:border-teal-500/50 transition-all">
                    <button onclick="deleteVolunteer('${v.id}')" class="absolute top-6 right-6 opacity-0 group-hover:opacity-100 transition-all w-10 h-10 bg-rose-500/10 text-rose-500 rounded-xl hover:bg-rose-500 hover:text-white flex items-center justify-center">
                        <i class="fa-solid fa-trash-can text-sm"></i>
                    </button>
                    <div class="w-14 h-14 bg-slate-900 rounded-2xl flex items-center justify-center font-black text-teal-400 border border-slate-800 text-xl">${v.name[0]}</div>
                    <div><p class="text-lg font-black text-white tracking-tight">${v.name}</p><p class="text-xs text-slate-500 font-medium">${v.district}</p></div>
                    <div class="flex flex-wrap gap-2">${v.skills.map(s => `<span class="text-[9px] px-3 py-1.5 bg-slate-900 rounded-lg border border-slate-800 text-slate-400 font-black uppercase tracking-widest">${s}</span>`).join('')}</div>
                </div>`; 
            });
        }

        async function runAIMatch() {
            const loader = document.getElementById('matching-loader'); const btn = document.getElementById('btn-run-match'); const results = document.getElementById('matches-results');
            loader.classList.remove('hidden'); btn.classList.add('hidden'); results.innerHTML = '';
            try {
                const res = await fetch('/volunteers/match', { method: 'POST' }); const data = await res.json();
                setTimeout(() => { 
                    loader.classList.add('hidden'); btn.classList.remove('hidden'); 
                    (data.matches || []).forEach(m => { 
                        results.innerHTML += `<div class="glass p-10 rounded-[48px] border-l-8 border-teal-500 space-y-5 hover:scale-[1.02] transition-transform">
                            <div class="flex justify-between items-start">
                                <div><h4 class="text-xl font-black text-white tracking-tight">${m.volunteer_name}</h4><p class="text-[10px] text-teal-400 font-black uppercase tracking-widest mt-1">${m.need_category}</p></div>
                                <span class="text-[10px] px-4 py-1.5 bg-slate-900 rounded-xl font-black uppercase text-white border border-slate-800">${m.priority}</span>
                            </div>
                            <p class="text-sm text-slate-400 font-medium leading-relaxed italic">"${m.task_summary}"</p>
                            <div class="bg-teal-500/5 p-5 rounded-2xl text-xs text-slate-400 font-medium border border-teal-500/10 flex gap-3">
                                <i class="fa-solid fa-brain text-teal-400 mt-1"></i>
                                <span><b>Gemini Logic:</b> ${m.match_reason}</span>
                            </div>
                        </div>`; 
                    }); 
                }, 1200);
            } catch (e) { loader.classList.add('hidden'); btn.classList.remove('hidden'); }
        }

        window.onload = () => {
            const saved = localStorage.getItem('vn_user_v2');
            if (saved) {
                currentUser = JSON.parse(saved);
                document.getElementById('login-overlay').style.display = 'none';
                document.getElementById('main-dashboard').style.display = 'flex';
                initDashboard();
            }
        };
    </script>
</body>
</html>"""




@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint. Returns status ok if the server is running."""
    return {"status": "ok"}


@app.get("/manifest.json", tags=["System"])
async def pwa_manifest():
    """PWA Web App Manifest — makes Volunite installable on Android/iOS."""
    from fastapi.responses import JSONResponse
    return JSONResponse({
        "name": "Volunite",
        "short_name": "Volunite",
        "description": "Unite. Serve. Impact. — AI-powered community needs intelligence.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f0c29",
        "theme_color": "#00BFA5",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "https://img.icons8.com/color/192/map-pin.png", "sizes": "192x192", "type": "image/png"},
            {"src": "https://img.icons8.com/color/512/map-pin.png", "sizes": "512x512", "type": "image/png"}
        ],
        "categories": ["productivity", "utilities"],
        "lang": "en-IN"
    })




# ─── Survey Endpoints ────────────────────────────────────────────────────────


@app.post("/surveys/submit", status_code=status.HTTP_201_CREATED, tags=["Surveys"])
async def submit_survey(survey_input: SurveySubmit):
    """
    Submit a new community need survey.

    Accepts survey data, computes urgency score via ML pipeline,
    and stores the entry in Firestore (or in-memory store in demo mode).
    """
    try:
        survey = Survey(
            location=survey_input.location,
            district=survey_input.district,
            state=survey_input.state,
            category=survey_input.category,
            description=survey_input.description,
            severity=survey_input.severity,
            affected_count=survey_input.affected_count,
            source=survey_input.source,
        )
        survey_dict = survey.model_dump()
        survey_dict["urgency_score"] = compute_urgency_score(survey_dict)

        survey_id = save_survey(survey_dict)
        logger.info(f"Survey submitted: {survey_id} | Urgency: {survey_dict['urgency_score']}")

        return {
            "message": "Survey submitted successfully",
            "survey_id": survey_id,
            "urgency_score": survey_dict["urgency_score"],
        }
    except Exception as e:
        logger.error(f"Error submitting survey: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit survey: {str(e)}",
        )


@app.post("/surveys/upload-csv", status_code=status.HTTP_201_CREATED, tags=["Surveys"])
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file containing multiple survey entries.

    Parses each row, computes urgency scores, and stores all entries.
    Expected CSV columns: district, state, category, description,
    severity, affected_count, latitude, longitude.
    """
    fname = (file.filename or "").lower()
    if not fname.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted.",
        )

    try:
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
            )
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        saved_count = 0
        errors = []

        for i, row in enumerate(reader):
            try:
                survey = Survey(
                    location={
                        "latitude": float(row.get("latitude", 0)),
                        "longitude": float(row.get("longitude", 0)),
                    },
                    district=row.get("district", "Unknown"),
                    state=row.get("state", "Maharashtra"),
                    category=row.get("category", "healthcare"),
                    description=row.get("description", ""),
                    severity=int(row.get("severity", 3)),
                    affected_count=int(row.get("affected_count", 1)),
                    source="csv_upload",
                )
                survey_dict = survey.model_dump()
                survey_dict["urgency_score"] = compute_urgency_score(survey_dict)
                save_survey(survey_dict)
                saved_count += 1
            except Exception as e:
                errors.append(f"Row {i + 1}: {str(e)}")

        return {
            "message": f"CSV processed: {saved_count} surveys saved",
            "saved_count": saved_count,
            "errors": errors,
        }
    except Exception as e:
        logger.error(f"CSV upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV: {str(e)}",
        )


@app.post("/surveys/ocr", status_code=status.HTTP_201_CREATED, tags=["Surveys"])
async def ocr_survey(file: UploadFile = File(...)):
    """
    Extract survey data from a paper survey image using OCR.

    Accepts JPG/PNG images, runs Google Cloud Vision OCR (or mock in demo mode),
    extracts survey fields, computes urgency score, and returns extracted data
    for user confirmation before saving.
    """
    ct = (file.content_type or "").lower()
    fname = (file.filename or "").lower()
    allowed_ct = {"image/jpeg", "image/png", "image/jpg"}
    allowed_ext = (".jpg", ".jpeg", ".png")
    if ct not in allowed_ct and not any(fname.endswith(ext) for ext in allowed_ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG/PNG images are accepted.",
        )

    try:
        image_bytes = await file.read()
        if len(image_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
            )
        extracted = extract_survey_from_image(image_bytes)
        extracted["urgency_score"] = compute_urgency_score(extracted)

        # Save to store
        save_survey(extracted)

        return {
            "message": "OCR extraction complete",
            "extracted_survey": extracted,
        }
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}",
        )


@app.get("/surveys/all", tags=["Surveys"])
async def get_surveys():
    """Return all survey entries from the data store."""
    try:
        surveys = get_all_surveys()
        return {"surveys": surveys, "count": len(surveys)}
    except Exception as e:
        logger.error(f"Error fetching surveys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch surveys: {str(e)}",
        )


@app.get("/surveys/clusters", tags=["Surveys"])
async def get_clusters():
    """
    Return K-Means clustered community needs.

    Runs the ML pipeline to cluster all surveys geographically,
    identifying hotspots of urgent needs.
    """
    try:
        surveys = get_all_surveys()
        if not surveys:
            return {"clusters": [], "message": "No surveys available for clustering."}

        clusters = cluster_needs(surveys)
        return {
            "clusters": clusters,
            "total_clusters": len(clusters),
            "total_surveys": len(surveys),
        }
    except Exception as e:
        logger.error(f"Clustering error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering failed: {str(e)}",
        )


@app.get("/surveys/urgent", tags=["Surveys"])
async def get_urgent_needs():
    """Return the top 10 most urgent community needs sorted by urgency score."""
    try:
        surveys = get_all_surveys()
        # Sort by urgency_score descending
        sorted_surveys = sorted(
            surveys,
            key=lambda s: float(s.get("urgency_score", 0)),
            reverse=True,
        )
        top_urgent = sorted_surveys[:10]
        return {"urgent_needs": top_urgent, "count": len(top_urgent)}
    except Exception as e:
        logger.error(f"Error fetching urgent needs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch urgent needs: {str(e)}",
        )


# ─── Volunteer Endpoints ─────────────────────────────────────────────────────


@app.post("/volunteers/register", status_code=status.HTTP_201_CREATED, tags=["Volunteers"])
async def register_volunteer(volunteer_input: VolunteerRegister):
    """Register a new volunteer with their skills, location, and availability."""
    try:
        volunteer = Volunteer(
            name=volunteer_input.name,
            phone=volunteer_input.phone,
            skills=volunteer_input.skills,
            available=volunteer_input.available,
            location=volunteer_input.location,
            district=volunteer_input.district,
            languages=volunteer_input.languages,
        )
        vol_dict = volunteer.model_dump()
        vol_id = save_volunteer(vol_dict)

        return {
            "message": "Volunteer registered successfully",
            "volunteer_id": vol_id,
        }
    except Exception as e:
        logger.error(f"Error registering volunteer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register volunteer: {str(e)}",
        )


@app.get("/volunteers/available", tags=["Volunteers"])
async def get_volunteers():
    """Get all currently available volunteers."""
    try:
        volunteers = get_available_volunteers()
        return {"volunteers": volunteers, "count": len(volunteers)}
    except Exception as e:
        logger.error(f"Error fetching volunteers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch volunteers: {str(e)}",
        )


@app.post("/volunteers/match", tags=["Volunteers"])
async def run_matching():
    """
    Run AI-powered volunteer-need matching.

    Fetches the most urgent community needs and available volunteers,
    then uses Gemini AI to produce optimal assignments.
    """
    try:
        surveys = get_all_surveys()
        volunteers = get_available_volunteers()

        if not surveys:
            return {"matches": [], "message": "No surveys available for matching."}
        if not volunteers:
            return {"matches": [], "message": "No volunteers available for matching."}

        # Get top urgent needs
        sorted_surveys = sorted(
            surveys,
            key=lambda s: float(s.get("urgency_score", 0)),
            reverse=True,
        )
        urgent_needs = sorted_surveys[:10]

        # Run Gemini matching
        matches = match_volunteers(urgent_needs, volunteers)

        # Save match results
        for match in matches:
            save_match_result(match)

        return {
            "matches": matches,
            "count": len(matches),
            "message": f"Matched {len(matches)} volunteers to urgent needs.",
        }
    except Exception as e:
        logger.error(f"Matching error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Volunteer matching failed: {str(e)}",
        )


# ─── Dashboard Endpoints ─────────────────────────────────────────────────────


@app.get("/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats():
    """
    Return summary statistics for the dashboard.

    Includes total surveys, active volunteers, count of urgent needs
    (urgency_score > 50), top category, and average urgency score.
    """
    try:
        surveys = get_all_surveys()
        volunteers = get_available_volunteers()

        if not surveys:
            return {
                "total_surveys": 0,
                "total_volunteers": len(volunteers),
                "urgent_needs": 0,
                "top_category": "N/A",
                "avg_urgency": 0.0,
            }

        urgency_scores = [float(s.get("urgency_score", 0)) for s in surveys]
        urgent_count = sum(1 for score in urgency_scores if score > 50)
        avg_urgency = round(sum(urgency_scores) / len(urgency_scores), 2) if urgency_scores else 0.0

        # Find top category
        from collections import Counter
        categories = [s.get("category", "unknown") for s in surveys]
        top_category = Counter(categories).most_common(1)[0][0] if categories else "N/A"
        category_counts = dict(Counter(categories))

        return {
            "total_surveys": len(surveys),
            "total_volunteers": len(volunteers),
            "active_volunteers": len(volunteers),
            "urgent_needs": urgent_count,
            "urgent_count": urgent_count,
            "top_category": top_category,
            "avg_urgency": avg_urgency,
            "category_breakdown": {
                "healthcare": category_counts.get("healthcare", 0),
                "food": category_counts.get("food", 0),
                "education": category_counts.get("education", 0),
                "sanitation": category_counts.get("sanitation", 0),
                "employment": category_counts.get("employment", 0),
            },
        }
    except Exception as e:
        logger.error(f"Error computing dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute stats: {str(e)}",
        )


# ─── Run with Uvicorn ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
