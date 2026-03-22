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
        answer, sources, confidence = await rag_answer(
            question=request.message,
            farm_context=request.farm_context,
            top_k=5
        )

        # XAI explanation sederhana (akan diperkaya di sistem penuh)
        xai = XAIExplanation(
            summary=f"Jawaban ini didasarkan pada {len(sources)} dokumen ilmiah pertanian Indonesia dengan tingkat keyakinan {int(confidence * 100)}%.",
            key_factors=[
                "Relevansi semantik dokumen RAG",
                "Konteks lahan pengguna",
                "Pengetahuan LLM tentang pertanian tropis"
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
