"""
User Model — SQLAlchemy ORM untuk table 'users' di Railway PostgreSQL
"""

from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.sql import func
import uuid
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        Enum("petani", "penyuluh", "peneliti", "admin", name="user_role"),
        default="petani",
        nullable=False
    )
    location = Column(String(200), nullable=True, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone or "",
            "email": self.email,
            "role": self.role,
            "location": self.location or "",
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
