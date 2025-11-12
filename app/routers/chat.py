from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.chat import ChatRequest, ChatResponse
from app.db.session import AsyncSessionLocal
from app.db import models
from app.services.llm import chat_llm
from app.services.retriever import vectorstore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

router = APIRouter(prefix="/chat", tags=["chat"])


# ✅ Async DB dependency
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 1️⃣ Retrieve last few chats for this user
    result = await db.execute(
        select(models.ChatHistory)
        .filter(models.ChatHistory.user_id == req.user_id)
        .order_by(models.ChatHistory.id.desc())
        .limit(5)
    )
    past_chats = result.scalars().all()

    # 2️⃣ Build memory object (conversation buffer)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    for c in reversed(past_chats):
        memory.chat_memory.add_user_message(c.question)
        memory.chat_memory.add_ai_message(c.answer)

    # 3️⃣ Create retriever (for document-based context)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # 4️⃣ Build conversational retrieval chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=chat_llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
    )

    # 5️⃣ Ask question with memory + retrieval
    result = chain.invoke({"question": req.question})

    # 6️⃣ Save new chat in DB
    new_chat = models.ChatHistory(
        user_id=req.user_id,
        question=req.question,
        answer=result.get("answer", "No response generated."),
    )
    db.add(new_chat)
    await db.commit()

    # 7️⃣ Collect document sources
    sources = []
    for d in result.get("source_documents", []):
        src = d.metadata.get("source")
        if src and src not in sources:
            sources.append(src)

    return ChatResponse(
        answer=result.get("answer", "No answer generated."),
        sources=sources,
    )
