"""
Database Setup — PostgreSQL via SQLAlchemy (Async)
Terhubung ke Railway PostgreSQL

Usage:
  from app.database import get_db, init_db
  async with get_db() as db:
      ...
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from app.config import DATABASE_URL
import asyncio

# ── Convert URL ───────────────────────────────────────────────────────────
# Railway PostgreSQL URL format: postgresql://user:pass@host:5432/db
# SQLAlchemy async needs: postgresql+asyncpg://...

def get_async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url

# ── Async Engine ──────────────────────────────────────────────────────────
ASYNC_DATABASE_URL = get_async_url(DATABASE_URL)

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,           # Set True untuk debug SQL queries
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # Test koneksi sebelum digunakan
    connect_args={
        "ssl": "require"  # Railway PostgreSQL memerlukan SSL
    } if "railway" in DATABASE_URL.lower() or "rlwy.net" in DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ── Base Model ────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass

# ── Dependency ────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency untuk mendapatkan sesi database."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ── Create All Tables ─────────────────────────────────────────────────────
async def init_db():
    """Buat semua tabel di database. Dipanggil saat startup backend."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] Tabel berhasil dibuat/diverifikasi di Railway PostgreSQL.")
