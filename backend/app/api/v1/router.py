from fastapi import APIRouter
from app.api.v1 import auth, consultation, diagnostic, farms, system

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms"])
api_router.include_router(consultation.router, prefix="/consultation", tags=["Consultation RAG"])
api_router.include_router(diagnostic.router, prefix="/diagnostic", tags=["Diagnostic XAI"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
