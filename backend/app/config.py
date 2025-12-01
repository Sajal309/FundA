"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    database_url: str = "postgresql://postgres:password@db:5432/sectorview"
    secret_key: str = "supersecret"
    alchemy_echo: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

