from aiogram import Bot

from core.config import BOT_TOKEN, PROXY, logger

from aiogram.client.session.aiohttp import AiohttpSession

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
