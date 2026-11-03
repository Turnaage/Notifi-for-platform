import aiohttp

from html import escape
from urllib.parse import urlparse

from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

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
                "<b>Пока нет доступных уроков</b>\n\n"
                "Возможно, ты уже завершил программу "
                "или новые материалы пока недоступны.",
                parse_mode="HTML",
            )
            return

    except (aiohttp.ClientError, TimeoutError):
        logger.exception(
            "Ошибка запроса следующего урока для пользователя %s",
            telegram_id,
        )

        await message.answer(
            "<b>Не удалось получить информацию об уроке</b>\n\n"
            "Платформа временно недоступна. "
            "Попробуй немного позже.",
            parse_mode="HTML",
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
            "<b>Не удалось открыть урок</b>\n\n"
            "Информация о материале временно недоступна. "
            "Попробуй позже.",
            parse_mode="HTML",
        )
        return

    parsed_url = urlparse(url)

    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        logger.warning(
            "Некорректная ссылка на урок для пользователя %s",
            telegram_id,
        )

        await message.answer(
            "Ссылка на урок временно недоступна. "
            "Попробуй позже."
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть урок",
                    url=url,
                )
            ]
        ]
    )

    safe_name = escape(str(name))

    await message.answer(
        "📚 <b>Твой следующий урок</b>\n\n"
        f"<b>{safe_name}</b>\n\n"
        "Продолжай обучение в основном курсе. "
        "Выдели немного времени, чтобы пройти следующий материал.",
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    logger.info(
        "Следующий урок успешно отправлен пользователю %s",
        telegram_id,
    )


@router.message(Command("next_lesson"))
@router.message(lambda message: message.text == "Следующий урок")
async def next_lesson_handler(message: Message):
    await send_next_lesson(message)
