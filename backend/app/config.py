from typing import Optional
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("gemini_api_key", "google_api_key")
    )
    gemini_model: str = "gemini-2.5-flash"
    database_url: str
    mongodb_uri: str
    google_client_id: str
    google_client_secret: str
    jwt_secret: str
    allowed_email_domain: str = "temple.edu"
    environment: str = "local"

    model_config = {"env_file": ".env"}


settings = Settings()
