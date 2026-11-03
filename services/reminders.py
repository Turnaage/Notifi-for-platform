import aiohttp
import asyncio

from html import escape
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from urllib.parse import urlparse

from schemas.user_settings import UserSettings
from database.db import SessionFactory
from database.models import Notification, User
from database.models import UserSettings as UserSettingsModel
from services.api import get_progress, get_next_lesson
from services.schedule import is_reminder_time
from core.config import logger, INACTIVITY_HOURS




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
        user = await session.scalar(
            select(User)
            .where(User.telegram_id == telegram_id)
            .options(
                joinedload(User.settings),
                selectinload(User.notifications),
            )
        )

        if user is None:
            logger.info("Пользователь отсутствует: %s", telegram_id)
            return

        if user.settings is None:
            logger.warning(
                "У пользователя %s отсутствуют настройки",
                telegram_id,
            )
            return

        settings = UserSettings.model_validate(user.settings)

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

        # В таблице notifications одна строка на пользователя,
        # время последнего напоминания хранится в updated_at.
        notification = user.notifications[0] if user.notifications else None
        last_sent = notification.updated_at if notification else None

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
            user = await session.scalar(
                select(User)
                .where(User.telegram_id == telegram_id)
                .options(selectinload(User.notifications))
            )

            if user is None:
                logger.warning(
                    "Пользователь %s исчез из базы после отправки",
                    telegram_id,
                )
                return

            notification = user.notifications[0] if user.notifications else None

            if notification is None:
                session.add(
                    Notification(
                        user_id=user.id,
                        updated_at=now,
                    )
                )
            else:
                notification.updated_at = now

    except (aiohttp.ClientError, asyncio.TimeoutError):
        logger.exception("Ошибка API для %s", telegram_id)

    except Exception:
        logger.exception("Ошибка напоминания для %s", telegram_id)



async def check_reminders(bot: Bot):
    logger.info("Начата общая проверка напоминаний")

    async with SessionFactory() as session:
        result = await session.scalars(
            select(User.telegram_id)
            .join(
                UserSettingsModel,
                UserSettingsModel.id == User.id,
            )
            .where(UserSettingsModel.reminders_enabled.is_(True))
        )
        telegram_ids = list(result.all())

    logger.info(
        "Найдено пользователей с включёнными напоминаниями: %s",
        len(telegram_ids),
    )

    for telegram_id in telegram_ids:
        await process_user_reminder(bot, telegram_id)

    logger.info("Общая проверка напоминаний завершена")
