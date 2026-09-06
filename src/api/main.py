"""
EASP - Enterprise AI Security Platform
FastAPI Microservice Main Entrypoint (AI 4 Component)
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

# Setup Base Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.api.routers import router as ai_router
from src.api.pipeline import EASPUnifiedAIPipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-warm models
    print("=" * 60)
    print("🚀 [EASP AI Service] Starting FastAPI Microservice (AI 4 - Kareem)")
    print("🛡️ Pre-warming Deep Learning, NLP, STT & DLP Models...")
    pipeline = EASPUnifiedAIPipeline.get_instance()
    print("✅ All AI Engines are online and ready to accept requests.")
    print("=" * 60)
    yield
    # Shutdown
    print("🛑 [EASP AI Service] Shutting down AI Microservice cleanly.")

app = FastAPI(
    title="EASP - Enterprise AI Security Platform API",
    description="""
    ## Enterprise AI Security Platform (EASP)
    **AI Integration & FastAPI Microservice Deliverable**
    * **Track:** AI / Data Science Track
    * **Role:** AI 4 (kareem) — AI Integration, FastAPI, Data Science Integration
    
    ### Capabilities:
    * 🎙️ **Voice Deepfake Detection:** Spectral profiling + Deep CNN audio analysis (AI 1 Integration).
    * 📝 **Speech-to-Text Transcription:** Faster-Whisper int8 multilingual speech recognition (AI 2 Integration).
    * 🔒 **Reversible Zero-Trust DLP:** AES-256 in-memory tokenization of PII and credentials (Cyber 2 Integration).
    * 🤖 **Prompt Injection & Social Engineering Detection:** NLP intent classification (AI 3 Integration).
    * ⚖️ **Unified Multi-Modal Risk & Policy Engine:** Composite 0-100 risk scoring with ALLOW/FLAG/BLOCK decisions (Cyber 3 Integration).
    * 📊 **SHAP Explainability & Telemetry:** Token feature attribution and latency tracking.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for CS 1 (Express Backend) & CS 2 (React Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AI Routers
app.include_router(ai_router)

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
