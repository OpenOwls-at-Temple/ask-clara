from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str
    mongodb_uri: str
    google_client_id: str
    google_client_secret: str
    jwt_secret: str
    allowed_email_domain: str = "temple.edu"
    environment: str = "local"

    model_config = {"env_file": ".env"}


settings = Settings()
