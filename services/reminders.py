from html import escape
from urllib.parse import urlparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone

import aiohttp
from aiogram import Bot
from sqlalchemy import select

from schemas.user_settings import UserSettings
from database.db import SessionFactory
from database.models import User
from services.api import get_progress, get_next_lesson
from services.schedule import is_reminder_time

logger = logging.getLogger(__name__)

INACTIVITY_HOURS = 24


def parse_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if dt.tzinfo is None:
        raise ValueError("Дата API должна содержать часовой пояс")

    return dt.astimezone(timezone.utc)



async def process_user_reminder(bot: Bot, telegram_id: int):
    now = datetime.now(timezone.utc)

    logger.info(
        "Начата проверка напоминания для пользователя %s",
        telegram_id,
    )

    async with SessionFactory() as session:
        user = await session.get(User, telegram_id)

        if user is None:
            logger.info("Пользователь отсутствует: %s", telegram_id)
            return

        settings = UserSettings.model_validate(user)

        if not settings.reminders_enabled:
            logger.info(
                "Напоминания отключены для пользователя %s",
                telegram_id,
            )
            return

        if not is_reminder_time(settings):
            logger.debug(
                "Сейчас не время отправки напоминания пользователю %s",
                telegram_id,
            )
            return

        interval_hours = settings.reminder_interval_hours
        last_sent = user.last_reminder_sent_at

        if last_sent:
            if last_sent.tzinfo is None:
                last_sent = last_sent.replace(tzinfo=timezone.utc)

            if now - last_sent < timedelta(hours=interval_hours):
                logger.info(
                    "Интервал напоминания ещё не истёк: %s",
                    telegram_id,
                )
                return

    try:
        progress = await get_progress(telegram_id)

        activity_value = progress.get("last_activity_at")
        if not activity_value:
            logger.warning(
                "API не вернул last_activity_at для пользователя %s",
                telegram_id,
            )
            return

        last_activity = parse_datetime(activity_value)

        if now - last_activity < timedelta(hours=INACTIVITY_HOURS):
            logger.info(
                "Недостаточный период без активности: %s",
                telegram_id,
            )
            return

        if progress.get("has_pending_review", False):
            logger.info(
                "Есть незавершённая проверка: %s",
                telegram_id,
            )
            return

        lesson = await get_next_lesson(telegram_id)

        if not lesson:
            logger.info(
                "Следующий урок не найден для пользователя %s",
                telegram_id,
            )
            return

        name = lesson.get("name")
        url = lesson.get("url")

        if not name or not url:
            logger.warning("Некорректный урок для %s", telegram_id)
            return

        parsed_url = urlparse(url)

        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            logger.warning("Некорректная ссылка на урок для %s", telegram_id)
            return

        safe_name = escape(name)
        safe_url = escape(url, quote=True)

        text = (
            "Пора продолжить обучение!\n\n"
            f"Следующий урок: <b>{safe_name}</b>\n\n"
            f'<a href="{safe_url}">Перейти к уроку</a>'
        )

        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode="HTML",
        )

        logger.info(
            "Напоминание успешно отправлено пользователю %s",
            telegram_id,
        )

        async with SessionFactory.begin() as session:
            user = await session.get(User, telegram_id)

            if user:
                user.last_reminder_sent_at = now

    except (aiohttp.ClientError, asyncio.TimeoutError):
        logger.exception("Ошибка API для %s", telegram_id)

    except Exception:
        logger.exception("Ошибка напоминания для %s", telegram_id)



async def check_reminders(bot: Bot):
    logger.info("Начата общая проверка напоминаний")

    async with SessionFactory() as session:
        result = await session.scalars(
            select(User.telegram_id).where(
                User.reminders_enabled.is_(True)
            )
        )
        telegram_ids = list(result.all())

    logger.info(
        "Найдено пользователей с включёнными напоминаниями: %s",
        len(telegram_ids),
    )

    for telegram_id in telegram_ids:
        await process_user_reminder(bot, telegram_id)

    logger.info("Общая проверка напоминаний завершена")
