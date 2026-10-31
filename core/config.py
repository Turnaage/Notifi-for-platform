import logging
from pathlib import Path

from aiogram import Router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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

"""         settings        """
BOT_TOKEN = settings.BOT_TOKEN
DATABASE_URL = settings.DATABASE_URL
API_BASE_URL = settings.API_BASE_URL.rstrip("/")
PROXY = settings.PROXY or None
API_TOKEN = settings.API_TOKEN

"""            logger               """
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"

MAX_LOG_SIZE = 5 * 1024 * 1024
BACKUP_COUNT = 5

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | "
    "%(name)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger(__name__)

"""        handler_config         """

router = Router()

REMINDER_INTERVALS = (24, 48, 72, 168)

REMINDER_SCHEDULES = {
    "after_work": {
        "name": "После работы",
        "weekday": ("18:00", "22:00"),
        "weekend": ("10:00", "20:00"),
    },
    "morning": {
        "name": "Утреннее",
        "weekday": ("07:00", "09:00"),
        "weekend": ("09:00", "12:00"),
    },
    "evening": {
        "name": "Вечернее",
        "weekday": ("18:00", "22:00"),
        "weekend": ("18:00", "22:00"),
    },
}

"""scheduler_config"""
scheduler = AsyncIOScheduler(timezone="UTC")