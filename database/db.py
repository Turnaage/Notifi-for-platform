
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.dialects.postgresql import insert

from core.config import DATABASE_URL, logger, REMINDER_INTERVALS
from database.models import User


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

async def ensure_user(telegram_id: int):
    """Создать пользователя, если его ещё нет."""
    try:
        async with get_db() as db:
            statement = (
                insert(User)
                .values(telegram_id=telegram_id)
                .on_conflict_do_nothing(
                    index_elements=[User.telegram_id]
                )
            )

            await db.execute(statement)
            await db.commit()
        logger.info("Пользователь %s проверен в базе данных", telegram_id)

    except Exception:
        logger.exception(
            "Ошибка создания пользователя %s",
            telegram_id,
        )
        raise


async def get_user(telegram_id: int) -> User | None:
    try:
        async with get_db() as db:
            user = await db.get(User, telegram_id)

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

        async with get_db() as db:
            user = await db.get(User, telegram_id)
            user.reminders_enabled = enabled
            await db.commit()
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

    if interval_hours not in REMINDER_INTERVALS:
        raise ValueError(
            f"Недопустимый интервал напоминаний: {interval_hours}"
        )


    try:
        async with get_db() as db:
            user = await db.get(User, telegram_id)

            if user is None:
                raise ValueError(
                    f"Пользователь {telegram_id} не найден"
                )

            user.reminder_interval_hours = interval_hours
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
    allowed_schedules = {
        "after_work",
        "morning",
        "evening",
    }

    if schedule_name not in allowed_schedules:
        raise ValueError(
            f"Недопустимое расписание: {schedule_name}"
        )


    try:
        async with get_db() as db:
            user = await db.get(User, telegram_id)

            if user is None:
                raise ValueError(
                    f"Пользователь {telegram_id} не найден"
                )

            user.reminder_schedule = schedule_name
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