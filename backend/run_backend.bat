@echo off
echo Mempersiapkan lingkungan virtual (venv)...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat

echo Menginstal dependencies...
pip install -r requirements.txt

echo Menjalankan FastAPI Server...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
