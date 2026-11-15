import os
import pytest

from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError
from dotenv import load_dotenv


load_dotenv()


@pytest.mark.asyncio
async def test_telegram_connection():
    token = os.getenv("BOT_TOKEN")
    proxy = os.getenv("PROXY")
    assert token, "BOT_TOKEN не найден в .env"

    bot = Bot(token=token, proxy=proxy)

    try:
        try:
            me = await bot.get_me()
        except TelegramNetworkError as error:
            pytest.skip(f"Telegram API недоступен: {error}")

        assert me.id
        assert me.username

        print(f"Подключение успешно: @{me.username}")

    finally:
        await bot.session.close()