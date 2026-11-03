from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from database.db import ensure_user
from core.config import logger, router


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Следующий урок"),
        ],
        [
            KeyboardButton(text="Настройки напоминаний"),
        ],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


@router.message(CommandStart())
async def start_handler(message: Message):
    telegram_id = message.from_user.id

    logger.info(
        "Пользователь %s выполнил команду /start",
        telegram_id,
    )

    try:
        await ensure_user(telegram_id)

        await message.answer(
            "<b>Добро пожаловать!</b> 👋\n\n"
            "Я помогу тебе сохранять регулярность обучения "
            "и напомню, когда пора вернуться к основному курсу.\n\n"
            "Ты можешь в любой момент открыть следующий урок "
            "или изменить настройки напоминаний.\n\n"
            "<b>Продолжим обучение?</b>",
            reply_markup=main_keyboard,
            parse_mode="HTML",
        )

        logger.info(
            "Главное меню отправлено пользователю %s",
            telegram_id,
        )

    except Exception:
        logger.exception(
            "Ошибка обработки команды /start для пользователя %s",
            telegram_id,
        )
        raise
