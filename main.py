from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import Base
from app.db.session import async_engine
from app.routers import chat, upload
import asyncio

# Create all tables at startup (only for dev/demo; use Alembic in production)
async def init_models():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(title="LangChain FAQ Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_credentials= True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(upload.router)

# ---- Startup Event ----
@app.on_event("startup")
async def on_startup():
    await init_models()

# ---- Root Endpoint ----
@app.get("/")
async def root():
    return {"status": "ok", "message": "FAQ Chatbot API running"}

