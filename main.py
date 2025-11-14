from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from app.db.base import Base
from app.db.session import async_engine,AsyncSessionLocal
from app.routers import chat, upload
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers.chat import process_chat
import asyncio

# In-memory chat history for UI
chat_history_ui = []

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

templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Store UI chat history
chat_history_ui = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials= True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(upload.router)

# Homepage for chat UI
@app.get("/chat-ui", response_class=HTMLResponse)
async def chat_ui(request:Request):
    return templates.TemplateResponse("chat.html", {"request": request, "chat_history": chat_history_ui})

@app.post("/chat-ui-message")
async def chat_ui_message(request: Request):
    data = await request.json()
    user_msg = data.get("message", "").strip()
    if user_msg == "":
        return JSONResponse({"reply": ""})

    # Store user message for UI
    chat_history_ui.append({"sender": "You", "message": user_msg})

    # Call backend chat processor
    async with AsyncSessionLocal() as db:
        response = await process_chat(user_id="user123", question=user_msg, db=db)

    # Store bot response for UI
    chat_history_ui.append({"sender": "Bot", "message": response.answer})

    return JSONResponse({"reply": response.answer})


@app.post("/chat-ui-clear")
async def chat_ui_clear():
    global chat_history_ui
    chat_history_ui = []
    return {"status": "ok", "message": "Chat cleared"}


# ---- Root Endpoint ----
@app.get("/")
async def root():
    return {"status": "ok", "message": "FAQ Chatbot API running"}

