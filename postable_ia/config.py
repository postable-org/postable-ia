import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    port: int = int(os.getenv("PORT", "8000"))
    trends_cache_ttl_hours: int = 5  # midpoint of 4-6 hours

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
