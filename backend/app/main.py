from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from dotenv import load_dotenv

# Tải file .env từ thư mục gốc của backend (phải làm TRƯỚC khi import app.core)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.agents.orchestrator import orchestrator
from app.core.database import init_db
from app.core.redis import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    try:
        await init_db()
        print("✅ Database tables initialized")
    except Exception as e:
        print(f"⚠️ Database init skipped: {e}")
    yield

app = FastAPI(title="Firestarter AI Backend", version="2.0.0", lifespan=lifespan)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "mistral"
    stream: bool = False

@app.get("/")
async def root():
    return {"status": "online", "message": "Firestarter AI Backend is running"}

@app.get("/api/health")
async def health():
    """Health check with DB/Redis status."""
    db_status = "unknown"
    redis_status = "unknown"
    
    try:
        from app.core.database import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    try:
        await redis_client.client.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)[:50]}"
    
    return {
        "status": "online",
        "database": db_status,
        "redis": redis_status
    }

@app.get("/api/models")
async def get_models():
    """Fetch available models from local Ollama."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch models from Ollama")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint using the Pentest Orchestrator."""
    try:
        content = await orchestrator.handle_request(
            user_prompt=request.messages[-1].content,
            model=request.model if request.model != "Multi-Model" else "mistral"
        )
        return {
            "message": {
                "role": "assistant",
                "content": content
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
