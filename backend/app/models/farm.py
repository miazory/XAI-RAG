"""
Farm Model — SQLAlchemy ORM untuk table 'farms'
"""

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
import uuid
from app.database import Base

class Farm(Base):
    __tablename__ = "farms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    area = Column(Float, nullable=False, default=1.0) # dalam hektar
    commodity = Column(String(50), nullable=False)
    growth_phase = Column(String(50), nullable=False)
    
    # Kondisi Tanah & Lingkungan (opsional)
    ph = Column(Float, nullable=True)
    nitrogen = Column(Float, nullable=True)
    phosphorus = Column(Float, nullable=True)
    potassium = Column(Float, nullable=True)
    
    # Penyimpanan foto base64 sementara (maks ~5MB biasanya muat di Text)
    image_base64 = Column(Text, nullable=True)
    
    # Arahan AI otomatis setelah ditambah/diedit
    ai_suggestion = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "areaHectare": self.area,
            "location": "",
            "commodity": self.commodity,
            "phase": self.growth_phase,
            "status": "baik" if not self.ai_suggestion else "perhatian",
            "alertMessage": self.ai_suggestion,
            "ph": self.ph,
            "nitrogen": self.nitrogen,
            "phosphorus": self.phosphorus,
            "potassium": self.potassium,
            "imageBase64": self.image_base64,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
