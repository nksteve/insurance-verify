from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://ivuser:ivpass_local@localhost:5432/insurance_verify"
    pverify_mock_mode: bool = True
    pverify_client_id: Optional[str] = None
    pverify_client_secret: Optional[str] = None
    secret_key: str = "demo-secret-key-change-in-prod"
    api_key: str = "demo-api-key"
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
