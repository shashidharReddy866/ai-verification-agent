from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.routes.verify_route import router as verify_router
from app.database.db import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    logger.info("Starting up — creating database tables...")
    try:
        create_tables()
        logger.info("Database tables ready.")
    except Exception as e:
        logger.warning(f"DB table creation failed (may already exist): {e}")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Verification Agent API",
    description=(
        "AI-powered candidate identity verification using Gemini Vision OCR. "
        "Extracts data from Aadhaar, PAN, Passport images and cross-checks "
        "against candidate-claimed data."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────
app.include_router(verify_router, prefix="/api/v1", tags=["Verification"])


# ── Health Check ───────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return JSONResponse({"status": "ok", "service": "Verification Agent API"})


@app.get("/", tags=["Health"])
def root():
    return JSONResponse({
        "message": "Verification Agent API is running.",
        "docs": "/docs",
        "health": "/health",
        "verify": "POST /api/v1/verify"
    })
