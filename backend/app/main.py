from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1.router import api_router
from app.config import ALLOWED_ORIGINS
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event: Initialize database tables
    await init_db()
    yield
    # Shutdown events can go here

app = FastAPI(
    title="IFS Agri API",
    description="Backend for IFS Agri Flutter App (XAI RAG)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to IFS Agri API!"}
