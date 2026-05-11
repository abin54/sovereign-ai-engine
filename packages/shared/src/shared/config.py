from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Security
    system_auth_token: Optional[str] = None
    audit_secret: str = "default-system-secret-key"
    
    # Telemetry
    otlp_endpoint: Optional[str] = None
    
    # LLM Keys
    openai_api_key: str = "mock-key"
    anthropic_api_key: str = "mock-key"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
