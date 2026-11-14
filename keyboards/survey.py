from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_survey_invite_keyboard(curator_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Пройти опрос",
                callback_data=f"survey:start:{curator_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отказаться",
                callback_data="survey:decline"
            )
        ]
    ])


def get_rating_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=str(i),
                callback_data=f"survey:rate:{i}"
            )
            for i in range(1, 6)
        ]
    ])

def get_test_survey_invite_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Пройти тестовый опрос",
                callback_data="survey:test:start"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отказаться",
                callback_data="survey:decline"
            )
        ]
    ])