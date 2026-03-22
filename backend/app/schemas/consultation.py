from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    farm_id: Optional[str] = None

class SourceModel(BaseModel):
    id: str
    title: str
    url: str
    relevanceScore: float

class ChatResponse(BaseModel):
    reply: str
    sources: List[SourceModel]
