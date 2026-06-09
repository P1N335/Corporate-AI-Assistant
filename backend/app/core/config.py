"""Конфигурация приложения. Все значения читаются из окружения / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Приложение
    app_name: str = "Corporate AI Assistant"
    log_level: str = "INFO"
    cors_origins: str = "*"

    # LLM (Ollama, OpenAI-совместимый API — путь /v1)
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen3:14b"
    llm_temperature: float = 0.2
    llm_timeout: int = 120

    # Embeddings (Ollama нативный API, без /v1)
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"

    # База данных
    database_url: str = "postgresql+psycopg2://corpai:corpai@localhost:5432/corpai"

    # Vector store
    chroma_mode: str = "server"  # "server" | "embedded"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection: str = "knowledge_base"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_top_k: int = 6

    # Очередь и фоновая обработка
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_queue: str = "document_processing"
    upload_dir: str = "./uploaded_files"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
