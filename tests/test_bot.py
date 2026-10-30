import os

import pytest
from aiogram import Bot


@pytest.mark.asyncio
async def test_telegram_connection():
    token = os.getenv("BOT_TOKEN")
    proxy = os.getenv("PROXY")

    assert token, "Переменная BOT_TOKEN не задана"

    bot = Bot(token=token, proxy=proxy)

    try:
        me = await bot.get_me()

        assert me.id > 0
        assert me.username is not None

    finally:
        await bot.session.close()