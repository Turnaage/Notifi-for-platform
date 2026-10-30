
import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from database.db import ensure_user


logger = logging.getLogger(__name__)

router = Router()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Следующий урок")],
        [KeyboardButton(text="Настройки")],
    ],
    resize_keyboard=True,
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
            "Привет! Я помогу тебе продолжать обучение "
            "и буду напоминать о занятиях.\n\n"
            "Выбери действие:",
            reply_markup=main_keyboard,
        )

        logger.info(
            "Приветственное сообщение отправлено пользователю %s",
            telegram_id,
        )

    except Exception:
        logger.exception(
            "Ошибка обработки команды /start для пользователя %s",
            telegram_id,
        )
        raise
