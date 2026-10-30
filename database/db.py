
import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import DATABASE_URL
from database.models import Base, User


logger = logging.getLogger(__name__)


engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """
    Проверить доступность базы данных.
    Структуру базы создаёт Alembic.
    """
    try:
        async with engine.connect() as connection:
            await connection.execute(select(1))

        logger.info("Подключение к базе данных проверено")

    except Exception:
        logger.exception("Ошибка подключения к базе данных")
        raise

async def close_db():
    try:
        await engine.dispose()
        logger.info("Подключение к базе данных закрыто")

    except Exception:
        logger.exception("Ошибка закрытия базы данных")
        raise


async def ensure_user(telegram_id: int):
    """Создать пользователя, если его ещё нет."""
    try:
        async with SessionFactory.begin() as session:
            statement = (
                insert(User)
                .values(telegram_id=telegram_id)
                .on_conflict_do_nothing(
                    index_elements=[User.telegram_id]
                )
            )

            await session.execute(statement)

        logger.info("Пользователь %s проверен в базе данных", telegram_id)

    except Exception:
        logger.exception(
            "Ошибка создания пользователя %s",
            telegram_id,
        )
        raise


async def get_user(telegram_id: int) -> User | None:
    try:
        async with SessionFactory() as session:
            user = await session.get(User, telegram_id)

        if user is None:
            logger.info("Пользователь %s не найден", telegram_id)

        return user

    except Exception:
        logger.exception(
            "Ошибка получения пользователя %s",
            telegram_id,
        )
        raise


async def set_reminders_enabled(
    telegram_id: int,
    enabled: bool,
):
    try:
        await ensure_user(telegram_id)

        async with SessionFactory.begin() as session:
            user = await session.get(User, telegram_id)
            user.reminders_enabled = enabled

        logger.info(
            "Настройка напоминаний пользователя %s изменена: %s",
            telegram_id,
            enabled,
        )

    except Exception:
        logger.exception(
            "Ошибка изменения настроек напоминаний пользователя %s",
            telegram_id,
        )
        raise


async def set_reminder_interval_hours(
    telegram_id: int,
    interval_hours: int,
):
    allowed_intervals = {24, 48, 72, 168}

    if interval_hours not in allowed_intervals:
        raise ValueError(
            f"Недопустимый интервал напоминаний: {interval_hours}"
        )

    await ensure_user(telegram_id)

    try:
        async with SessionFactory.begin() as session:
            user = await session.get(User, telegram_id)

            if user is None:
                raise ValueError(
                    f"Пользователь {telegram_id} не найден"
                )

            user.reminder_interval_hours = interval_hours

        logger.info(
            "Интервал напоминаний пользователя %s установлен: %s часов",
            telegram_id,
            interval_hours,
        )

    except Exception:
        logger.exception(
            "Ошибка изменения интервала напоминаний пользователя %s",
            telegram_id,
        )
        raise

async def set_reminder_schedule(
    telegram_id: int,
    schedule_name: str,
):
    allowed_schedules = {
        "after_work",
        "morning",
        "evening",
    }

    if schedule_name not in allowed_schedules:
        raise ValueError(
            f"Недопустимое расписание: {schedule_name}"
        )

    await ensure_user(telegram_id)

    try:
        async with SessionFactory.begin() as session:
            user = await session.get(User, telegram_id)

            if user is None:
                raise ValueError(
                    f"Пользователь {telegram_id} не найден"
                )

            user.reminder_schedule = schedule_name

        logger.info(
            "Расписание напоминаний пользователя %s изменено: %s",
            telegram_id,
            schedule_name,
        )

    except Exception:
        logger.exception(
            "Ошибка изменения расписания пользователя %s",
            telegram_id,
        )
        raise