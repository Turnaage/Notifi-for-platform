import asyncio

from aiogram import Dispatcher
from aiogram.types import BotCommand

from scheduler import start_scheduler, scheduler

from core.logging_config import setup_logging
from core.bot import create_bot
from database.db import close_db
from core.config import logger, router
import handlers.settings
import handlers.start
import handlers.next_lesson
import handlers.unknown

dp = Dispatcher()

dp.include_router(router)


async def main():
    aiogram_bot = None

    setup_logging()

    logger.info("Запуск приложения Notify_py")

    try:
        logger.info("Подключение к базе данных выполнено")

        aiogram_bot = create_bot()

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

        await aiogram_bot.delete_webhook(drop_pending_updates=True)
        logger.info("Очередь старых обновлений сброшена")

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
