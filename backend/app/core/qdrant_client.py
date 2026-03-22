"""
Qdrant Client — Koneksi ke Qdrant Cloud Vector Database
Digunakan untuk menyimpan dan mencari dokumen pengetahuan pertanian (RAG)

CATATAN ARSITEKTUR:
- Qdrant = menyimpan VECTOR EMBEDDINGS dokumen pertanian (jurnal, panduan, dll)
- Bukan untuk menyimpan akun pengguna (user accounts menggunakan in-memory/SQLite)
- Saat nyambung ke Qdrant Cloud, dokumen disimpan sebagai vektor untuk pencarian semantik
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME
from typing import List, Dict, Optional
import uuid
import hashlib

# ── Qdrant Client Instance ───────────────────────────────────────────────
def get_qdrant_client() -> QdrantClient:
    """Membuat koneksi ke Qdrant Cloud."""
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30
    )

# ── Collection Setup ─────────────────────────────────────────────────────
def ensure_collection_exists(client: QdrantClient, vector_size: int = 768):
    """
    Memastikan koleksi 'ifs_knowledge' sudah ada di Qdrant Cloud.
    Dibuat otomatis dengan dimensi 768 (sesuai model Gemini text-embedding-004).
    """
    try:
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if QDRANT_COLLECTION_NAME not in collection_names:
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"[Qdrant] Koleksi '{QDRANT_COLLECTION_NAME}' berhasil dibuat.")
        else:
            print(f"[Qdrant] Koleksi '{QDRANT_COLLECTION_NAME}' sudah ada.")
    except Exception as e:
        print(f"[Qdrant] Error saat mengecek/membuat koleksi: {e}")

# ── Insert Documents ─────────────────────────────────────────────────────
def insert_knowledge_documents(documents: List[Dict]) -> bool:
    """
    Menyimpan dokumen pengetahuan ke Qdrant.
    
    Setiap dokumen harus punya:
    - text: str         → konten dokumen
    - title: str        → judul
    - source: str       → sumber (jurnal, panduan, dll)
    - commodity: str    → komoditas (padi, jagung, dll) — untuk filter
    - vector: List[float] → embedding dari model, dimuat dari luar
    """
    try:
        client = get_qdrant_client()
        ensure_collection_exists(client)

        points = []
        for doc in documents:
            # Generate deterministic ID dari teks
            doc_id = str(uuid.UUID(hashlib.md5(doc["text"].encode()).hexdigest()))
            points.append(
                PointStruct(
                    id=doc_id,
                    vector=doc["vector"],
                    payload={
                        "text": doc["text"],
                        "title": doc["title"],
                        "source": doc.get("source", ""),
                        "commodity": doc.get("commodity", ""),
                        "type": doc.get("type", "general"),
                        "year": doc.get("year", 2024),
                    }
                )
            )

        client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=points
        )
        print(f"[Qdrant] {len(points)} dokumen berhasil disimpan ke Qdrant Cloud.")
        return True
    except Exception as e:
        print(f"[Qdrant] Gagal insert dokumen: {e}")
        return False

# ── Search Documents ─────────────────────────────────────────────────────
def search_knowledge(
    query_vector: List[float],
    commodity_filter: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    Mencari dokumen relevan dari Qdrant Cloud berdasarkan vektor query.
    
    Args:
        query_vector: Embedding dari pertanyaan user
        commodity_filter: Filter komoditas (opsional)
        top_k: Jumlah dokumen yang dikembalikan
    
    Returns:
        List dokumen relevan dengan teks dan metadata
    """
    try:
        client = get_qdrant_client()

        # Build filter jika ada komoditas
        search_filter = None
        if commodity_filter:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="commodity",
                        match=MatchValue(value=commodity_filter)
                    )
                ]
            )

        results = client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True
        )

        return [
            {
                "text": r.payload.get("text", ""),
                "title": r.payload.get("title", ""),
                "source": r.payload.get("source", ""),
                "commodity": r.payload.get("commodity", ""),
                "type": r.payload.get("type", ""),
                "year": r.payload.get("year"),
                "score": r.score
            }
            for r in results
        ]
    except Exception as e:
        print(f"[Qdrant] Gagal search dokumen: {e}")
        return []

# ── Collection Info ──────────────────────────────────────────────────────
def get_collection_info() -> Dict:
    """Mendapatkan informasi koleksi Qdrant Cloud."""
    try:
        client = get_qdrant_client()
        info = client.get_collection(QDRANT_COLLECTION_NAME)
        return {
            "name": QDRANT_COLLECTION_NAME,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
        }
    except Exception as e:
        return {"error": str(e)}
