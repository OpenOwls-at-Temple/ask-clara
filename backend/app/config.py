from typing import Optional
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider selection — set one of the keys below and point llm_provider at it
    llm_provider: str = "anthropic"  # anthropic | gemini | deepseek
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("gemini_api_key", "google_api_key")
    )
    gemini_model: str = "gemini-2.5-flash"
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    database_url: str
    mongodb_uri: str
    google_client_id: str
    google_client_secret: str
    jwt_secret: str
    allowed_email_domain: str = "temple.edu"
    environment: str = "local"
    frontend_origin: str = "http://localhost:5173"

    model_config = {"env_file": ".env"}


settings = Settings()
