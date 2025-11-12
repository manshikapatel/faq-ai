from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.db import models
from app.routers import chat
from app.routers import upload



# Create tables on startup (simple alternative to Alembic for demo)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LangChain FAQ Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(upload.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "FAQ Chatbot API running"}


