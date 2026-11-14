from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_keyboard_next_less(url):
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

    return keyboard