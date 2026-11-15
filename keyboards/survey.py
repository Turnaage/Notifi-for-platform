from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_survey_invite_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Пройти опрос",
                    callback_data="survey:start",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отказаться",
                    callback_data="survey:decline",
                )
            ],
        ]
    )


def get_rating_keyboard(question: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=str(score),
                    callback_data=f"survey:rate:{question}:{score}",
                )
                for score in range(1, 6)
            ]
        ]
    )


def get_retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Повторить отправку",
                    callback_data="survey:retry",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отказаться",
                    callback_data="survey:decline",
                )
            ],
        ]
    )


def get_test_survey_invite_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Пройти тестовый опрос",
                    callback_data="survey:test:start",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отказаться",
                    callback_data="survey:decline",
                )
            ],
        ]
    )
