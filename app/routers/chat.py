from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse
from app.db.session import SessionLocal
from app.db import models
from app.services.llm import chat_llm
from app.services.retriever import vectorstore, search_similar
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

router = APIRouter(prefix="/chat", tags=["chat"])

# Simple DB session dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Custom RAG prompt
prompt = PromptTemplate.from_template(
    """
You are a helpful FAQ assistant. Use ONLY the provided context to answer.
If the answer is not in the context, say you don't know.

Question: {question}

Context:
{context}

Answer:
"""
)

@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    chain = RetrievalQA.from_chain_type(
        llm=chat_llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )

    # result = chain.invoke({"query": req.question})
    result = chain.run(req.question)  # simpler, returns answer string
    source_docs = retriever.get_relevant_documents(req.question)  # get sources separately

    # Persist chat
    db.add(models.ChatHistory(
        user_id=req.user_id,
        question=req.question,
        answer=result["result"],
    ))
    db.commit()
    '''
    sources = []
    for d in result.get("source_documents", []):
        src = d.metadata.get("source")
        if src and src not in sources:
            sources.append(src)
'''
    sources = list({d.metadata.get("source") for d in source_docs if d.metadata.get("source")})


    return ChatResponse(answer=result["result"], sources=sources)