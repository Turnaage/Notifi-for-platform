import asyncio

from aiogram import Bot

from core.config import BOT_TOKEN, logger
from services.survey import send_monthly_surveys


async def main():
    bot = Bot(token=BOT_TOKEN)

    try:
        await send_monthly_surveys(bot)
        logger.info(
            "Запуск рассылки"
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())