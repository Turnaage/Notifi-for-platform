from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    API_BASE_URL: str

    PROXY: str | None = None
    API_TOKEN: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

BOT_TOKEN = settings.BOT_TOKEN
DATABASE_URL = settings.DATABASE_URL
API_BASE_URL = settings.API_BASE_URL.rstrip("/")
PROXY = settings.PROXY or None
API_TOKEN = settings.API_TOKEN