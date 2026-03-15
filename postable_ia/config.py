from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    port: int = Field(default=8000, validation_alias=AliasChoices("PORT", "port"))
    trends_cache_ttl_hours: int = 5  # midpoint of 4-6 hours
    image_model: str = Field(
        default="gemini-3.1-flash-image-preview",
        validation_alias="IMAGE_MODEL",
    )
    image_max_retries: int = Field(default=3, validation_alias="IMAGE_MAX_RETRIES")
    image_retry_backoff_seconds: float = Field(
        default=1.0, validation_alias="IMAGE_RETRY_BACKOFF_SECONDS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
