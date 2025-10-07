# core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
# DATABASE_URL should look like: postgresql+psycopg://USER:PASS@HOST:5432/DB

def _normalize_db_url(url: str) -> str:
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url

class Settings(BaseSettings):
    DATABASE_URL: str
    ENV: str = "dev"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, **data):
        super().__init__(**data)
        object.__setattr__(self, "DATABASE_URL", _normalize_db_url(self.DATABASE_URL))

@lru_cache
def get_settings() -> Settings:
    return Settings()
