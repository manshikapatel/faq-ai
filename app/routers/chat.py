from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.chat import ChatRequest, ChatResponse
from app.db.session import AsyncSessionLocal
from app.db import models
from app.services.llm import chat_llm,fallback_chat_llm
from app.services.retriever import vectorstore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import asyncio
from openai import RateLimitError, OpenAIError

router = APIRouter(prefix="/chat", tags=["chat"])

# -------------------------------
# 1️⃣ ASYNC DB Dependency
# -------------------------------
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

# -------------------------------
# 2️⃣ Safe Chain Invocation
# -------------------------------
async def safe_invoke_chain(chain, question, max_retries=5):
    """Invokes LangChain ConversationalRetrievalChain safely with retries on 429."""
    retries = 0
    wait_time = 2
    
    while retries <= max_retries:
        try:
            return await chain.ainvoke({"question": question})
        except RateLimitError:
            retries += 1
            print(f"Rate limit hit. Retrying in {wait_time}s... (Attempt {retries})")
            await asyncio.sleep(wait_time)
            wait_time *= 2  # exponential backoff
        except OpenAIError as e:
            print(f"OpenAI error: {e}")
            break
    return None
# -------------------------------
# 3️⃣ Reusable chat logic
# -------------------------------
async def process_chat(user_id: str, question: str, db: AsyncSession):
    # Load last 5 messages
    result = await db.execute(
        select(models.ChatHistory)
        .filter(models.ChatHistory.user_id == user_id)
        .order_by(models.ChatHistory.id.desc())
        .limit(10)
    )
    past_chats = result.scalars().all()

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    for c in reversed(past_chats):
        memory.chat_memory.add_user_message(c.question)
        memory.chat_memory.add_ai_message(c.answer)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    chain = ConversationalRetrievalChain.from_llm(
        llm=chat_llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        output_key="answer",
    )

    result_data = await safe_invoke_chain(chain, question)

    # fallback to GPT-3.5
    if result_data is None:
        fallback_chain = ConversationalRetrievalChain.from_llm(
            llm=fallback_chat_llm,
            retriever=retriever,
            memory=memory.copy(),
            return_source_documents=True,
            output_key="answer",
        )
        result_data = await safe_invoke_chain(fallback_chain, question)
        if result_data is None:
            return ChatResponse(answer="Failed to generate response due to rate limits.", sources=[])

    try:
        answer_text = result_data.get("answer", "")
        source_docs = result_data.get("source_documents", [])
    except Exception:
        answer_text = str(result_data)
        source_docs = []

    # Save to DB
    new_chat = models.ChatHistory(
        user_id=user_id,
        question=question,
        answer=answer_text,
    )
    db.add(new_chat)
    await db.commit()

    sources = []
    for d in source_docs:
        src = d.metadata.get("source")
        if src and src not in sources:
            sources.append(src)

    return ChatResponse(answer=answer_text, sources=sources)
'''
# -------------------------------
# 3️⃣ Chat Endpoint
# -------------------------------
@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    
    # Load last 5 messages
    result = await db.execute(
        select(models.ChatHistory)
        .filter(models.ChatHistory.user_id == req.user_id)
        .order_by(models.ChatHistory.id.desc())
        .limit(5)
    )
    past_chats = result.scalars().all()

    # Memory object
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    # Put old chat history into memory
    for c in reversed(past_chats):
        memory.chat_memory.add_user_message(c.question)
        memory.chat_memory.add_ai_message(c.answer)

    # Build retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Create chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=chat_llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        output_key="answer",
    )

    # Run chain safely
    result_data = await safe_invoke_chain(chain, req.question)

    # Optional: fallback to GPT-3.5 if GPT-4 fails
    if result_data is None:
        print("Falling back to GPT-3.5...")
        
        fallback_chain = ConversationalRetrievalChain.from_llm(
            llm=fallback_chat_llm,  # GPT-3.5 llm
            retriever=retriever,
            memory=memory.copy(),
            return_source_documents=True,
            output_key="answer",
        )
        result_data = await safe_invoke_chain(fallback_chain, req.question)
        
        if result_data is None:
            return ChatResponse(answer="Failed to generate response due to rate limits.", sources=[])
        
    # -------------------------------
    # Extract final answer safely
    # -------------------------------
    try:
        answer_text = result_data.get("answer", "")
        source_docs = result_data.get("source_documents", [])
    except Exception:
        answer_text = str(result_data)
        source_docs = []
        
        
    # -------------------------------
    # Save to DB
    # -------------------------------
    new_chat = models.ChatHistory(
        user_id=req.user_id,
        question=req.question,
        answer=answer_text,
    )
    db.add(new_chat)
    await db.commit()

    # -------------------------------
    # Extract unique sources
    # -------------------------------
    sources = []
    for d in source_docs:
        src = d.metadata.get("source")
        if src and src not in sources:
            sources.append(src)
        
    # -------------------------------
    # Final Response
    # -------------------------------
    return ChatResponse(
        answer=answer_text,
        sources=sources,
    )
'''
# -------------------------------
# 4️⃣ Existing chat endpoint
# -------------------------------
@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    user_id = str(req.user_id)
    return await process_chat(user_id, req.question, db)