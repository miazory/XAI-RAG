from pydantic import BaseModel
from typing import Optional

class FarmResponse(BaseModel):
    id: str
    name: str
    area: float
    commodity: str
    status: str
    cropPhase: str
    alertMessage: Optional[str] = None
