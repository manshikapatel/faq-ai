# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_openai import ChatOpenAI
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


from app.core.config import settings

# embeddings = OpenAIEmbeddings(
    # model=settings.openai_embed_model,
    # openai_api_key=settings.openai_api_key,
# )
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


chat_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=0.1,
    openai_api_key=settings.openai_api_key, 
)