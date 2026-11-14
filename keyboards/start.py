from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📖 Следующий урок"),
        ],
        [
            KeyboardButton(text="⚙️ Настройки напоминаний"),
        ],
    ],
    resize_keyboard=True,
    is_persistent=True,
)