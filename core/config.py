from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str  # e.g., postgres://... (Heroku will set this)
    ENV: str = "dev"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()
