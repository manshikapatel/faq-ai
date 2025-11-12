from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from app.core.config import settings
from app.services.llm import embeddings
from dotenv import load_dotenv

load_dotenv()

_client = QdrantClient(host="localhost", port=6333)

def ensure_collection(collection_name: str = settings.qdrant_collection, vector_size: int = 384):
    existing = [c.name for c in _client.get_collections().collections]
    if collection_name not in existing:
        print(f"Creating collection: {collection_name}")
        _client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
    else:
        print(f"Collection already exists: {collection_name}")

ensure_collection()

# ✅ Correct LangChain wrapper
vectorstore = QdrantVectorStore(
    client=_client,
    collection_name=settings.qdrant_collection,
    embedding=embeddings,
)

print("Number of vectors in collection:", _client.count(settings.qdrant_collection).count)

def search_similar(query: str, k: int = 4) -> List[dict]:
    docs = vectorstore.similarity_search(query, k=k)
    return [{"page_content": d.page_content, "source": d.metadata.get("source")} for d in docs]
