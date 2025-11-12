
# ingest/ingest_documents.py
from pathlib import Path
from app.services.retriever import vectorstore, ensure_collection
from app.services.llm import embeddings
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


SUPPORTED_EXTS = {".pdf", ".md"}

def load_docs(data_dir: Path):
    docs = []
    for p in data_dir.rglob("*"):
        if p.suffix.lower() not in SUPPORTED_EXTS:
            continue
        print(f" Loading file: {p}")
        loader = PyPDFLoader(str(p)) if p.suffix.lower() == ".pdf" else UnstructuredMarkdownLoader(str(p))
        ds = loader.load()
        
        
        # Debug: Print first 1-2 pages of loaded content
        for i, d in enumerate(ds[:2]):
            print(f"Document {i+1} preview: {d.page_content[:200]}...\n")

        for d in ds:
            d.metadata = d.metadata or {}
            d.metadata["source"] = str(p)
        docs.extend(ds)
    return docs


def chunk_docs(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    
    # Debug: Show first 3 chunks
    for i, chunk in enumerate(chunks[:3]):
        print(f"Chunk {i+1}: {chunk.page_content[:100]}...\n")
    return chunks



def main():
    print("Ensuring collection exists...")
    ensure_collection()
    data_dir = Path("data")  # folder where PDFs/MD files are stored
    docs = load_docs(data_dir)
    print(f" Loaded {len(docs)} documents")

    chunks = chunk_docs(docs)
    print(f" Split into {len(chunks)} chunks")

    if chunks:
        print("Adding chunks to vectorstore...")
        vectorstore.add_documents(chunks)
        count = vectorstore.client.count(vectorstore.collection_name).count
        print(f"Vectors in collection after adding: {count}")
        print("Bulk ingestion completed and stored in Qdrant.")
    else:
        print("No chunks to add. Check if documents contain text!")


if __name__ == "__main__":
    main()

#python -m ingest.ingest_documents