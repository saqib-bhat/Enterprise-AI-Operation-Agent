from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_provider: str = "groq"
    groq_api_key: str | None = None
    groq_model: str = "gpt-4.1-mini"
    database_url: str = "sqlite:///./data/operations.db"
    vector_store_path: str = "./vector_store"
    mlflow_enabled: bool = False
    log_level: str = "INFO"
    max_llm_requests_per_session: int = 10
    max_output_tokens: int = 512
    request_timeout: int = 30
    max_retries: int = 2
    max_verification_attempts: int = 2

    # pydantic-settings v1+ config
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
