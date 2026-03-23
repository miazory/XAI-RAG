from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import google.generativeai as genai

from app.database import get_db
from app.models.user import User
from app.models.farm import Farm
from app.api.v1.auth import get_current_user
from app.config import GEMINI_API_KEY, GEMINI_MODEL

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────────────
class FarmInput(BaseModel):
    name: str
    area: float
    commodity: str
    growth_phase: str
    ph: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    image_base64: Optional[str] = None

# ── Helper ───────────────────────────────────────────────────────────────
async def generate_ai_suggestion(farm_data: FarmInput) -> str:
    """Generate agronomy suggestion using Gemini."""
    if not GEMINI_API_KEY:
        return "Pertahankan kelembapan tanah dan lakukan pemantauan hama rutin."
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""
        Kamu adalah pakar Agronomi untuk IFS Agri.
        Diberikan data Lahan:
        - Komoditas: {farm_data.commodity}
        - Fase Pertumbuhan: {farm_data.growth_phase}
        - Luas: {farm_data.area} Hektar
        - pH Tanah: {farm_data.ph or 'Belum diukur'}
        
        Berikan 2 kalimat saran singkat (maksimal 30 kata) untuk mengoptimalkan lahan ini pada fase pertumbuhannya saat ini.
        Gunakan gaya bahasa santai tapi profesional.
        """
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[Farm AI Error]: {e}")
        return "Jaga kebersihan lahan dan pantau cuaca secara berkala."

# ── Endpoints ────────────────────────────────────────────────────────────
@router.get("/", response_model=List[dict])
async def get_my_farms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.user_id == current_user.id))
    farms = result.scalars().all()
    return [farm.to_dict() for farm in farms]

@router.post("/")
async def create_farm(
    request: FarmInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ai_suggestion = await generate_ai_suggestion(request)
    
    new_farm = Farm(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=request.name,
        area=request.area,
        commodity=request.commodity,
        growth_phase=request.growth_phase,
        ph=request.ph,
        nitrogen=request.nitrogen,
        phosphorus=request.phosphorus,
        potassium=request.potassium,
        image_base64=request.image_base64,
        ai_suggestion=ai_suggestion
    )
    db.add(new_farm)
    await db.flush()
    await db.refresh(new_farm)
    
    return new_farm.to_dict()

@router.put("/{farm_id}")
async def update_farm(
    farm_id: str,
    request: FarmInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == current_user.id))
    farm = result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Lahan tidak ditemukan atau tidak ada akses")
        
    ai_suggestion = await generate_ai_suggestion(request)
    
    farm.name = request.name
    farm.area = request.area
    farm.commodity = request.commodity
    farm.growth_phase = request.growth_phase
    farm.ph = request.ph
    farm.nitrogen = request.nitrogen
    farm.phosphorus = request.phosphorus
    farm.potassium = request.potassium
    
    # Jika dikirim image baru ganti, jika tidak biarkan image yg lama asalkan tidak None eksplisit (tergantung implementasi mobile)
    if request.image_base64 is not None:
        farm.image_base64 = request.image_base64
        
    farm.ai_suggestion = ai_suggestion
    
    await db.flush()
    await db.refresh(farm)
    
    return farm.to_dict()

@router.delete("/{farm_id}")
async def delete_farm(
    farm_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == current_user.id))
    farm = result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Lahan tidak ditemukan atau tidak ada akses")
        
    await db.delete(farm)
    return {"id": farm_id, "deleted": True}
