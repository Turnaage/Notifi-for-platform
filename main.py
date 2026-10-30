
import asyncio
import logging

from aiogram import Dispatcher
from aiogram.types import BotCommand

from core.logging_config import setup_logging
from core.bot import aiogram_bot
from database.db import init_db, close_db
from handlers.start import router as start_router
from handlers.settings import router as settings_router
from handlers.next_lesson import router as next_lesson_router
from scheduler import start_scheduler, scheduler


logger = logging.getLogger(__name__)

dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(next_lesson_router)
dp.include_router(settings_router)


async def main():
    setup_logging()

    logger.info("Запуск приложения Notify_py")

    try:
        await init_db()
        logger.info("Подключение к базе данных выполнено")

        await aiogram_bot.set_my_commands([
            BotCommand(
                command="start",
                description="Запустить бота",
            ),
            BotCommand(
                command="next_lesson",
                description="Следующий урок",
            ),
            BotCommand(
                command="settings",
                description="Настройки",
            ),
        ])

        logger.info("Команды Telegram зарегистрированы")

        start_scheduler(aiogram_bot)
        logger.info("Планировщик запущен")

        await dp.start_polling(aiogram_bot)

    except Exception:
        logger.exception("Критическая ошибка приложения")
        raise

    finally:
        logger.info("Завершение работы приложения")

        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Планировщик остановлен")

        await close_db()
        logger.info("Соединение с базой данных закрыто")

        await aiogram_bot.session.close()
        logger.info("Сессия Telegram закрыта")


if __name__ == "__main__":
    asyncio.run(main())
