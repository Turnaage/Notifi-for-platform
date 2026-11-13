from aiogram import Bot
from aiohttp_socks import ProxyConnector
from aiogram.client.session.aiohttp import AiohttpSession


from core.config import BOT_TOKEN, PROXY, logger

def create_bot() -> Bot:
    if PROXY:
        proxy_url = PROXY if "://" in PROXY else f"http://{PROXY}"

        session = AiohttpSession(
        proxy=proxy_url,
        )

        logger.info(f"Бот будет использовать прокси: {proxy_url.split('@')[-1]}")
    else:
        session = AiohttpSession()

    aiogram_bot = Bot(
        token=BOT_TOKEN,
        session=session,
    )

    logger.info("Объект Telegram-бота создан")
    return aiogram_bot


