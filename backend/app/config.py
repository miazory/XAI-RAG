"""
IFS Agri Backend — Configuration
Membaca semua settings dari .env file
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# ── App ──────────────────────────────────────────────────────
APP_NAME: str = os.getenv("APP_NAME", "IFS Agri API")
DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

# ── Database (Railway PostgreSQL) ────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ifs_agri")

# ── Redis (Railway Redis) ────────────────────────────────────
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

# ── JWT ──────────────────────────────────────────────────────
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "fallback_secret_ganti_ini_di_produksi")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# ── Qdrant Cloud (Vector Database untuk RAG) ─────────────────
QDRANT_URL: str = os.getenv(
    "QDRANT_URL",
    "https://d4dda93c-f968-4e5f-8d1d-5a92d3444c72.us-east4-0.gcp.cloud.qdrant.io"
)
QDRANT_API_KEY: str = os.getenv(
    "QDRANT_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.YR8wXF9DQa69jgXUE0JTU-YRrBxhtLaE6K3bnMeY3_I"
)
QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "ifs_knowledge")

# ── LLM ──────────────────────────────────────────────────────
ACTIVE_LLM: str = os.getenv("ACTIVE_LLM", "gemini")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyAgV5F9NNawC0tRh8ZDa0BcGd4nHOX8u4c")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ── Production API URL (setelah deploy di Railway) ────────────
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://ifs-agri.pages.dev")

# ── CORS ─────────────────────────────────────────────────────
_origins_env = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS: List[str] = (
    [o.strip() for o in _origins_env.split(",") if o.strip()]
    if _origins_env
    else [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://10.0.2.2:8000",
        "https://ifs-agri.pages.dev",   # Cloudflare Pages
        "*",
    ]
)
