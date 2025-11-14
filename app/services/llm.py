from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings
import openai

from app.core.config import settings


embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=settings.openai_api_key,
)

#embeddings = HuggingFaceEmbeddings(
#    model_name="sentence-transformers/all-MiniLM-L6-v2"
#)


chat_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=0.1,
    openai_api_key=settings.openai_api_key, 
)

# Optional fallback to GPT-3.5
fallback_chat_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.1,
    openai_api_key=settings.openai_api_key,
)

# ✅ Helper to safely catch rate limit errors
RateLimitError = openai.RateLimitError
OpenAIError = openai.OpenAIError
