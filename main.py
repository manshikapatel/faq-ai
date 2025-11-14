from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from app.db.base import Base
from app.db.session import async_engine
from app.routers import chat, upload
import asyncio

# ---- Lifespan handler replaces deprecated on_event ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables initialized successfully.")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

    yield  # The app runs while this yields

    # Shutdown
    await async_engine.dispose()
    print("🧹 Database connection closed.")

app = FastAPI(title="LangChain FAQ Chatbot", version="1.0.0",description="An AI-enabled FAQ chatbot API powered by LangChain & OpenAI",lifespan= lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials= True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(upload.router)

# ---- Root Endpoint ----
@app.get("/")
async def root():
    return {"status": "ok", "message": "FAQ Chatbot API running"}

