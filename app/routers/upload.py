#Auto ingest file when upload file...
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from ingest.ingest_documents import load_docs, chunk_docs, SUPPORTED_EXTS
from app.services.retriever import vectorstore, ensure_collection
from app.services.llm import embeddings

router = APIRouter(prefix="/upload", tags=["upload"])
UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and MD files are supported"
        )

    # Save uploaded file
    save_path = UPLOAD_DIR / file.filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ingest into Qdrant
    docs = load_docs(UPLOAD_DIR)  # load all docs from /data
    chunks = chunk_docs(docs)
    ensure_collection()
    vectorstore.add_documents(chunks)

    return {
        "filename": file.filename,
        "chunks_added": len(chunks),
        "message": "File uploaded and ingested successfully"
    }

