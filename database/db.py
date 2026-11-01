from sqlalchemy import select
from contextlib import asynccontextmanager
from sqlalchemy.orm import joinedload, selectinload

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import User, UserSettings
from core.config import (
    DATABASE_URL,
    logger,
    REMINDER_INTERVALS,
    allowed_schedules,
)




engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db():
    async with SessionFactory() as db:
        yield db

async def close_db():
    await engine.dispose()


async def ensure_user(telegram_id: int) -> None:
    """Создать пользователя и его настройки, если их ещё нет."""

    try:
        async with get_db() as db:
            user = await db.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )

            if user is None:
                user = User(telegram_id=telegram_id)
                db.add(user)
                await db.flush()

            if user.settings is None:
                user.settings = UserSettings()

            await db.commit()

        logger.info(
            "Пользователь %s проверен в базе данных",
            telegram_id,
        )

    except Exception:
        logger.exception(
            "Ошибка создания пользователя %s",
            telegram_id,
        )
        raise



async def get_user(telegram_id: int) -> User | None:
    try:
        async with get_db() as db:
            user = await db.scalar(
                select(User)
                .where(User.telegram_id == telegram_id)
                .options(
                    joinedload(User.settings),
                    selectinload(User.notifications),
                )
            )

        if user is None:
            logger.info("Пользователь %s не найден", telegram_id)

        return user

    except Exception:
        logger.exception(
            "Ошибка получения пользователя %s",
            telegram_id,
        )
        raise

async def get_user_with_settings(db, telegram_id: int) -> User:
    user = await db.scalar(
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(joinedload(User.settings))
    )

    if user is None:
        raise ValueError(f"Пользователь {telegram_id} не найден")

    if user.settings is None:
        user.settings = UserSettings()

    return user

async def set_reminders_enabled(
    telegram_id: int,
    enabled: bool,
) -> None:
    try:
        async with get_db() as db:
            user = await get_user_with_settings(db, telegram_id)

            if user:
                user.settings.reminders_enabled = enabled

                await db.commit()

                logger.info(
                    "Настройка напоминаний пользователя %s изменена: %s",
                    telegram_id,
                    enabled,
                )
            else:
                logger.info(
                    "Пользователь %s не найден в базе",
                    telegram_id,
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
) -> None:

    if interval_hours not in REMINDER_INTERVALS:
        raise ValueError(
            f"Недопустимый интервал напоминаний: {interval_hours}"
        )


    try:
        async with get_db() as db:
            user = await get_user_with_settings(db, telegram_id)

            if user is None:
                raise ValueError(
                    f"Пользователь {telegram_id} не найден"
                )

            user.settings.reminder_interval_hours = interval_hours
            await db.commit()

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

    if schedule_name not in allowed_schedules:
        raise ValueError(
            f"Недопустимое расписание: {schedule_name}"
        )


    try:
        async with get_db() as db:
            user = await get_user_with_settings(db, telegram_id)

            if user is None:
                raise ValueError(
                    f"Пользователь {telegram_id} не найден"
                )

            user.settings.reminder_schedule = schedule_name
            await db.commit()

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