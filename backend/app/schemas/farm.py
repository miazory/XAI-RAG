from pydantic import BaseModel
from typing import Optional

class FarmResponse(BaseModel):
    id: str
    name: str
    areaHectare: float
    location: str
    commodity: str
    status: str
    phase: str
    alertMessage: Optional[str] = None
    ph: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    imageBase64: Optional[str] = None
