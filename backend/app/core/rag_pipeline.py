"""
RAG Pipeline — Menggunakan Gemini Embeddings API + Qdrant Cloud
Menggantikan sentence-transformers (terlalu besar untuk Railway free tier)

Gemini embeddings:
  Model: models/text-embedding-004
  Output: 768 dimensi
  Gratis: yes (sama dengan API key Gemini yang ada)
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from app.config import ACTIVE_LLM, GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL, QDRANT_COLLECTION_NAME

# ── Gemini Embedding (ganti sentence-transformers) ─────────────────────────
async def get_gemini_embedding(text: str) -> List[float]:
    """
    Embed teks menggunakan Google Gemini text-embedding-004 (768 dimensi).
    Gratis dengan limit quota harian yang cukup untuk research.
    """
    if not GEMINI_API_KEY:
        return _fallback_embedding(text)
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query",  # Untuk query
        )
        return result["embedding"]
    except Exception as e:
        print(f"[Embedding] Gemini error: {e}. Fallback ke hash embedding.")
        return _fallback_embedding(text)

async def get_gemini_embedding_for_document(text: str) -> List[float]:
    """Embed dokumen (untuk indexing, task_type berbeda dari query)."""
    if not GEMINI_API_KEY:
        return _fallback_embedding(text)
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",  # Untuk dokumen yang diindex
        )
        return result["embedding"]
    except Exception as e:
        print(f"[Embedding Doc] Gemini error: {e}. Fallback ke hash embedding.")
        return _fallback_embedding(text)

def _fallback_embedding(text: str, dim: int = 768) -> List[float]:
    """Fallback hash-based embedding jika Gemini tidak tersedia."""
    import hashlib, math
    vector = []
    for i in range(dim):
        h = int(hashlib.md5(f"{text}_{i}".encode()).hexdigest(), 16)
        vector.append(math.sin(h / 1e15) * 0.5)
    mag = sum(x**2 for x in vector) ** 0.5
    return [x / mag for x in vector] if mag > 0 else vector

# ── Prompt Template ──────────────────────────────────────────────────────
RAG_PROMPT = """Anda adalah ASISTEN PERTANIAN CERDAS IFS Agri untuk petani Indonesia.

Tugas:
- Jawab berdasarkan dokumen ilmiah yang diberikan (jika ada)
- Gunakan bahasa Indonesia yang mudah dipahami petani
- JANGAN mengarang informasi yang tidak ada di konteks
- Sebutkan sumber jika tersedia

{context_section}

Pertanyaan petani: {question}

Berikan jawaban yang jelas, praktis, dan mudah dipahami dengan poin-poin konkret:"""

# ── LLM Call ─────────────────────────────────────────────────────────────
async def call_llm(prompt: str) -> str:
    """Memanggil LLM: Gemini (aktif) atau Groq (backup)."""
    if ACTIVE_LLM == "gemini" and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                )
            )
            return response.text or "Maaf, tidak ada jawaban."
        except Exception as e:
            return f"[Gemini Error] {e}"

    elif ACTIVE_LLM == "groq" and GROQ_API_KEY:
        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=GROQ_API_KEY)
            resp = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=800
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"[Groq Error] {e}"

    return _mock_response(prompt)

def _mock_response(prompt: str) -> str:
    """Mock fallback saat tidak ada API key."""
    if any(k in prompt.lower() for k in ["hama", "wereng", "ulat"]):
        return "**PHT**: Monitor tiap 3-4 hari, gunakan musuh alami, insektisida hanya jika di atas ambang batas ekonomi.\n\n*Sumber: Panduan PHT Kementan RI*"
    elif any(k in prompt.lower() for k in ["pupuk", "nitrogen"]):
        return "**Pemupukan Padi**: Urea 250 kg/ha dibagi 3x: tanam, anakan (21 HST), primordia (45 HST).\n\n*Sumber: BPTP Sumbar*"
    return "Silakan konsultasikan dengan penyuluh setempat atau gunakan fitur Diagnostik untuk analisis lebih mendalam."

# ── Main RAG Function ─────────────────────────────────────────────────────
async def rag_answer(
    question: str,
    farm_context: Optional[Dict] = None,
    top_k: int = 5
) -> Tuple[str, List[Dict], float]:
    """
    RAG dengan Gemini Embeddings + Qdrant + Gemini LLM.
    Returns: (answer, sources, confidence)
    """
    # 1. Embed pertanyaan via Gemini
    query_vector = await get_gemini_embedding(question)

    # 2. Cari dokumen di Qdrant
    sources = []
    context_section = ""
    confidence = 0.65

    try:
        from app.core.qdrant_client import search_knowledge
        commodity = farm_context.get("commodity") if farm_context else None
        docs = search_knowledge(query_vector, commodity_filter=commodity, top_k=top_k)

        if docs:
            context_texts = [
                f"[Sumber: {d['title']}]\n{d['text']}" for d in docs
            ]
            context_section = f"Gunakan konteks dokumen berikut:\n\n{chr(10).join(context_texts)}\n---"
            sources = [{
                "title": d["title"],
                "source": d.get("source", ""),
                "score": d.get("score", 0.0),
                "type": d.get("type", ""),
                "year": d.get("year"),
            } for d in docs]
            confidence = min(0.98, docs[0].get("score", 0.65) if docs else 0.65)
        else:
            context_section = "Jawab berdasarkan pengetahuan umum pertanian Indonesia."
            sources = [{"title": "Pengetahuan Umum Pertanian Indonesia", "source": "Kementan RI", "score": 0.65, "type": "guide", "year": 2024}]
    except Exception as e:
        print(f"[RAG] Qdrant error: {e}")
        context_section = "Jawab berdasarkan pengetahuan umum pertanian Indonesia."
        sources = [{"title": "Pengetahuan Umum Pertanian Indonesia", "source": "Kementan RI", "score": 0.65, "type": "guide", "year": 2024}]

    # 3. Build prompt & generate jawaban
    prompt = RAG_PROMPT.format(context_section=context_section, question=question)
    answer = await call_llm(prompt)

    return answer, sources, confidence
