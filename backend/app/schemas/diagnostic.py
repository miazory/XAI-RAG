from pydantic import BaseModel
from typing import List

class DiagnosticRequest(BaseModel):
    farm: str
    description: str
    hasImage: bool

class ShapFeature(BaseModel):
    name: str
    value: float
    impact: str

class DiagnosticResponse(BaseModel):
    diseaseName: str
    confidenceScore: float
    severity: str
    recommendation: str
    xaiFeatures: List[ShapFeature]
