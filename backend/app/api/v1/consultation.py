"""
Consultation API — RAG Chat dengan Qdrant + LLM
Endpoint utama untuk chat konsultasi pertanian berbasis XAI-RAG
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.rag_pipeline import rag_answer

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    farm_id: Optional[str] = None
    farm_context: Optional[dict] = None  # {"commodity": "padi", "location": "..."}
    conversation_id: Optional[str] = None
    language: str = "id"

class SourceResponse(BaseModel):
    title: str
    source: str = ""
    score: float = 0.0
    type: str = ""
    year: Optional[int] = None

class XAIExplanation(BaseModel):
    summary: str
    key_factors: list[str] = []

class ChatResponse(BaseModel):
    reply: str
    sources: list[SourceResponse] = []
    confidence: float = 0.0
    xai_explanation: Optional[XAIExplanation] = None
    conversation_id: Optional[str] = None

# ── Endpoints ────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Endpoint konsultasi RAG utama.
    Mengambil dokumen dari Qdrant Cloud lalu generate jawaban via LLM.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong")

    try:
        import google.generativeai as genai
        import os
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY tidak ditemukan di environment")
            
        genai.configure(api_key=api_key)
        
        # Bypass RAG, langsung gunakan LLM
        model = genai.GenerativeModel("gemini-pro")
        
        prompt = f"""
        Kamu adalah AI Assistant Pertanian untuk sistem IFS Agri (Integrated Farming System).
        Saat ini fitur RAG (Retrieval-Augmented Generation) sedang dinonaktifkan sementara.
        Jawablah pertanyaan berikut dengan singkat, jelas, dan akurat berdasarkan pengetahuan dasar pertanianmu.
        
        Pertanyaan: {request.message}
        """
        
        response = model.generate_content(prompt)
        answer = response.text
        
        # Mock source since we bypass RAG
        sources = [
            {"title": "Pengetahuan Dasar Gemini AI", "score": 1.0}
        ]
        confidence = 0.95

        # XAI explanation sederhana
        xai = XAIExplanation(
            summary="Saat ini menggunakan Gemini Agent secara langsung. Fitur analisis dokumen RAG dinonaktifkan untuk sementara.",
            key_factors=[
                "Pengetahuan umum model LLM Gemini",
                "Prompt Assistant Pertanian"
            ]
        )

        return ChatResponse(
            reply=answer,
            sources=[SourceResponse(**s) for s in sources],
            confidence=confidence,
            xai_explanation=xai,
            conversation_id=request.conversation_id or "conv-demo-001"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses pertanyaan: {str(e)}")

@router.get("/history")
async def get_history():
    """Ambil riwayat konsultasi (mock untuk prototype)."""
    return {
        "consultations": [
            {
                "id": "c-001",
                "question": "Bagaimana cara mengatasi hama wereng coklat?",
                "answer_preview": "Pengendalian wereng coklat dapat dilakukan dengan...",
                "created_at": "2024-01-15T14:30:00Z",
                "confidence": 0.87
            },
            {
                "id": "c-002",
                "question": "Dosis pupuk urea untuk padi IR64?",
                "answer_preview": "Dosis rekomendasi pupuk urea untuk padi IR64...",
                "created_at": "2024-01-14T09:15:00Z",
                "confidence": 0.91
            }
        ],
        "total": 2
    }

@router.post("/{message_id}/feedback")
async def submit_feedback(message_id: str, rating: int, helpful: bool):
    """Simpan feedback user (mock untuk prototype)."""
    return {"message": "Feedback berhasil disimpan", "message_id": message_id}
