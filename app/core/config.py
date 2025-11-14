import os
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    env: str = os.getenv("ENV", "dev")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "*")

    POSTGRES_USER: str
    POSTGRES_PASSWORD:str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    
    database_url: str = None 

    # Qdrant
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", 6333))
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "faqs")

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_embed_model: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"  # <-- allows extra env vars without error
    )
    
    def __post_init__(self):
        # Dynamically set database_url based on other fields
        self.database_url = (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()
