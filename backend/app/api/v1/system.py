"""
System Status & Qdrant Info Endpoint
"""

from fastapi import APIRouter
from app.config import QDRANT_URL, QDRANT_COLLECTION_NAME, ACTIVE_LLM

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": "IFS Agri API",
        "version": "1.0.0-prototype",
        "llm_provider": ACTIVE_LLM,
    }

@router.get("/qdrant-info")
async def qdrant_info():
    """Info koneksi dan koleksi Qdrant Cloud."""
    try:
        from app.core.qdrant_client import get_qdrant_client, get_collection_info
        client = get_qdrant_client()
        # Test koneksi
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        info = get_collection_info() if QDRANT_COLLECTION_NAME in collection_names else {
            "status": "collection_not_found",
            "message": f"Koleksi '{QDRANT_COLLECTION_NAME}' belum dibuat. Jalankan endpoint /seed-demo-data untuk mengisi data awal."
        }
        
        return {
            "qdrant_url": QDRANT_URL,
            "collections_available": collection_names,
            "ifs_collection": info,
        }
    except Exception as e:
        return {
            "qdrant_url": QDRANT_URL,
            "status": "error",
            "detail": str(e)
        }

@router.post("/seed-demo-data")
async def seed_demo_data():
    """
    Inisialisasi koleksi Qdrant dengan data demo pertanian.
    Panggil sekali untuk mengisi Qdrant Cloud dengan dokumen awal.
    """
    try:
        from app.core.qdrant_client import get_qdrant_client, ensure_collection_exists, insert_knowledge_documents
        from app.core.rag_pipeline import get_gemini_embedding_for_document
        
        client = get_qdrant_client()
        ensure_collection_exists(client, vector_size=768)
        
        # Demo knowledge documents (without vectors first)
        demo_docs = [
            {
                "text": "Wereng coklat (Nilaparvata lugens) adalah hama utama padi sawah di Indonesia. Pengendalian terpadu dilakukan dengan rotasi varietas tahan, penggunaan musuh alami seperti laba-laba, dan insektisida sistemik imidakloprid atau buprofezin pada populasi tinggi di atas 15 ekor per rumpun.",
                "title": "Panduan Pengendalian Wereng Coklat Padi",
                "source": "BPTP Jawa Tengah, 2023",
                "commodity": "padi",
                "type": "guide",
                "year": 2023,
            },
            {
                "text": "Penyakit Blas (Pyricularia oryzae) menyerang padi pada kelembaban tinggi di atas 80% dan suhu 20-28°C. Gejala: bercak berlian coklat pada daun. Pengendalian: fungisida trisiklazol 75 WP dosis 0.5 kg/ha, aplikasi 2x selang 7 hari. Varietas tahan: Inpari 32, Ciherang.",
                "title": "Pedoman Pengendalian Penyakit Blas Padi",
                "source": "Balitbangtan Kementan RI, 2024",
                "commodity": "padi",
                "type": "journal",
                "year": 2024,
            },
            {
                "text": "Pemupukan padi sawah berimbang: Urea 250-300 kg/ha dibagi 3 kali pemberian: saat tanam 50%, anakan aktif 30%, primordia 20%. SP-36 100 kg/ha diberikan seluruhnya saat tanam. KCl 75 kg/ha diberikan 50% saat tanam dan 50% di primordia.",
                "title": "Rekomendasi Pemupukan Padi Sawah Irigasi",
                "source": "BPTP Sumatera Barat, 2024",
                "commodity": "padi",
                "type": "guide",
                "year": 2024,
            },
            {
                "text": "Kekurangan Nitrogen pada tanaman padi ditandai dengan daun menguning dimulai dari daun tua (klorosis). pH tanah ideal untuk padi adalah 5.5-7.0. Lakukan uji tanah minimal 2 musim sekali. Perbaiki dengan perukan organik 2 ton/ha sebelum tanam.",
                "title": "Diagnosis Kekurangan Hara Tanaman Padi",
                "source": "Balai Penelitian Tanah, 2023",
                "commodity": "padi",
                "type": "research",
                "year": 2023,
            },
            {
                "text": "Cabai merah (Capsicum annuum) rentan terhadap penyakit antraknosa (Colletotrichum acutatum). Gejala: bercak hitam cekung pada buah. Pencegahan: sanitasi kebun, hindari kelembaban berlebih, fungisida mankozeb 80 WP dosis 2 g/L air, semprot 7 hari sekali.",
                "title": "Pengendalian Penyakit Antraknosa Cabai",
                "source": "BPTP Jawa Barat, 2024",
                "commodity": "cabai",
                "type": "guide",
                "year": 2024,
            },
            {
                "text": "Integrated Farming System (IFS) atau Sistem Pertanian Terpadu mengintegrasikan tanaman pangan, hortikultura, dan peternakan dalam satu manajemen lahan. Di Sumatera Barat, sistem ini terbukti meningkatkan pendapatan petani 35% dan efisiensi pupuk 20% berdasarkan studi UNAND 2023.",
                "title": "Integrated Farming System di Sumatera Barat",
                "source": "Universitas Andalas, 2023",
                "commodity": "general",
                "type": "research",
                "year": 2023,
            },
        ]
        
        # Generate vectors
        for doc in demo_docs:
            doc["vector"] = await get_gemini_embedding_for_document(doc["text"])
        
        success = insert_knowledge_documents(demo_docs)
        
        if success:
            return {
                "status": "success",
                "message": f"{len(demo_docs)} dokumen demo berhasil disimpan ke Qdrant Cloud",
                "collection": QDRANT_COLLECTION_NAME,
                "documents_seeded": len(demo_docs)
            }
        else:
            return {"status": "failed", "message": "Gagal menyimpan ke Qdrant, cek logs backend"}
        
    except Exception as e:
        return {"status": "error", "detail": str(e)}
