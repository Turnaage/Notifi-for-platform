
import logging

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from core.config import BOT_TOKEN, PROXY


logger = logging.getLogger(__name__)

if PROXY:
    session = AiohttpSession(
    proxy=PROXY
    )
else:
    session = AiohttpSession()

aiogram_bot = Bot(
    token=BOT_TOKEN,
    session=session,
)

logger.info("Объект Telegram-бота создан")
