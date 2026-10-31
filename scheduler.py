
from aiogram import Bot

from services.reminders import check_reminders
from core.config import logger, scheduler



def start_scheduler(bot: Bot):
    if scheduler.running:
        logger.warning(
            "Повторный запуск планировщика пропущен: он уже работает"
        )
        return

    try:
        scheduler.add_job(
            check_reminders,
            trigger="interval",
            minutes=15,
            args=[bot],
            id="learning_reminders",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        scheduler.start()

        logger.info(
            "Планировщик запущен. Проверка напоминаний каждые 15 минут"
        )

    except Exception:
        logger.exception("Ошибка запуска планировщика")
        raise
