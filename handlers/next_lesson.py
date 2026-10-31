
from html import escape

import aiohttp
from aiogram.filters import Command
from aiogram.types import Message

from services.api import get_next_lesson
from core.config import logger, router


async def send_next_lesson(message: Message):
    telegram_id = message.from_user.id

    logger.info(
        "Запрошен следующий урок пользователем %s",
        telegram_id,
    )

    try:
        lesson = await get_next_lesson(telegram_id)

        if not lesson:
            logger.info(
                "Следующий урок отсутствует для пользователя %s",
                telegram_id,
            )

            await message.answer(
                "Сейчас нет доступных следующих уроков."
            )
            return

        name = lesson.get("name")
        url = lesson.get("url")

        if not name or not url:
            logger.warning(
                "API вернул некорректный урок для пользователя %s",
                telegram_id,
            )

            await message.answer(
                "Не удалось получить данные урока. Попробуй позже."
            )
            return

        safe_name = escape(name)
        safe_url = escape(url, quote=True)

        await message.answer(
            f"Следующий урок: <b>{safe_name}</b>\n\n"
            f'<a href="{safe_url}">Перейти к уроку</a>',
            parse_mode="HTML",
        )

        logger.info(
            "Следующий урок успешно отправлен пользователю %s",
            telegram_id,
        )

    except (aiohttp.ClientError, TimeoutError):
        logger.exception(
            "Ошибка запроса следующего урока для пользователя %s",
            telegram_id,
        )

        await message.answer(
            "Не удалось связаться с платформой. Попробуй позже."
        )

    except Exception:
        logger.exception(
            "Неожиданная ошибка при получении урока для пользователя %s",
            telegram_id,
        )

        await message.answer(
            "Произошла ошибка. Попробуй позже."
        )


@router.message(Command("next_lesson"))
@router.message(lambda message: message.text == "Следующий урок")
async def next_lesson_handler(message: Message):
    await send_next_lesson(message)
