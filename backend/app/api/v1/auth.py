"""
Auth API — Real JWT + PostgreSQL (Railway)
Menggunakan python-jose untuk JWT, bcrypt untuk hashing password, SQLAlchemy untuk PostgreSQL

Demo users (sudah tersimpan di PostgreSQL via seed endpoint):
  petani@demo.com   / demo123
  penyuluh@demo.com / demo123
  peneliti@demo.com / demo123
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from app.database import get_db
from app.models.user import User

router = APIRouter()
security = HTTPBearer()

# ── Password Hashing ──────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ── JWT ───────────────────────────────────────────────────────────────────
def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Optional[str]:
    """Decode JWT dan kembalikan user_id (sub)."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# ── Auth Dependency ───────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kedaluwarsa")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    return user

# ── Schemas ──────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    phone_or_email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    phone: str = ""
    email: str
    password: str
    role: str = "petani"
    location: str = ""

# ── Endpoints ────────────────────────────────────────────────────────────
@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    identifier = request.phone_or_email.lower().strip()

    # Cari user berdasarkan email atau telepon
    result = await db.execute(
        select(User).where(
            or_(User.email == identifier, User.phone == identifier)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Email atau nomor telepon tidak terdaftar")

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Kata sandi salah")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akun tidak aktif")

    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }

@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = request.email.lower().strip()

    # Cek duplikat email
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")

    # Cek duplikat telepon jika diisi
    if request.phone:
        existing_phone = await db.execute(select(User).where(User.phone == request.phone))
        if existing_phone.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Nomor telepon sudah terdaftar")

    new_user = User(
        id=str(uuid.uuid4()),
        name=request.name,
        phone=request.phone or None,
        email=email,
        hashed_password=hash_password(request.password),
        role=request.role,
        location=request.location,
    )
    db.add(new_user)
    await db.flush()   # Flush agar ID assigned, commit dilakukan di get_db()

    token = create_access_token(new_user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user.to_dict(),
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()

@router.post("/seed-demo-users")
async def seed_demo_users(db: AsyncSession = Depends(get_db)):
    """Isi akun demo ke PostgreSQL. Panggil sekali setelah deploy."""
    demo_users = [
        {"email": "petani@demo.com", "name": "Budi Santoso", "phone": "08123456789", "role": "petani", "location": "Padang, Sumbar"},
        {"email": "penyuluh@demo.com", "name": "Ibu Ratna Sari", "phone": "08234567890", "role": "penyuluh", "location": "Bukittinggi, Sumbar"},
        {"email": "peneliti@demo.com", "name": "Dr. Ahmad Fauzi", "phone": "08345678901", "role": "peneliti", "location": "Universitas Andalas, Padang"},
    ]
    
    created = []
    for u in demo_users:
        existing = await db.execute(select(User).where(User.email == u["email"]))
        if not existing.scalar_one_or_none():
            user = User(id=str(uuid.uuid4()), hashed_password=hash_password("demo123"), **u)
            db.add(user)
            created.append(u["email"])

    return {"message": f"{len(created)} demo users berhasil dibuat", "created": created}
