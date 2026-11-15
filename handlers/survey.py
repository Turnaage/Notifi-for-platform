from aiogram import F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from core.config import router, logger, TEST_TELEGRAM_ID
from keyboards.survey import (
    get_rating_keyboard,
    get_retry_keyboard,
)
from schemas.survey_states import SurveyStates, Survey
from services.api import send_survey


SURVEY_QUESTIONS = (
    "1. Насколько вы довольны работой куратора?",
    "2. Насколько куратор помогал вам в обучении?",
    "3. Насколько вы довольны коммуникацией с куратором?",
)

STATE_BY_QUESTION = {
    1: SurveyStates.question_1,
    2: SurveyStates.question_2,
    3: SurveyStates.question_3,
}

QUESTION_BY_STATE = {
    state.state: question
    for question, state in STATE_BY_QUESTION.items()
}


async def _answer(
    callback: CallbackQuery,
    text: str | None = None,
    show_alert: bool = False,
) -> None:
    try:
        await callback.answer(text=text, show_alert=show_alert)
    except TelegramBadRequest:
        logger.debug(
            "Не удалось ответить на callback %s: он уже устарел",
            callback.id,
        )


async def _edit_message(
    callback: CallbackQuery,
    text: str,
    reply_markup=None,
) -> None:
    if callback.message is None:
        return

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest:
        logger.exception(
            "Не удалось отредактировать сообщение опроса %s",
            callback.message.message_id,
        )


async def _start_survey(
    callback: CallbackQuery,
    state: FSMContext,
    is_test: bool,
) -> None:
    await state.update_data(
        answers=[],
        is_test=is_test,
        payload=None,
    )
    await state.set_state(SurveyStates.question_1)

    await _edit_message(
        callback,
        SURVEY_QUESTIONS[0],
        get_rating_keyboard(1),
    )


async def _submit_survey(
    callback: CallbackQuery,
    state: FSMContext,
    payload: dict,
) -> None:
    await state.set_state(SurveyStates.sending)

    await _edit_message(
        callback,
        "Отправляю оценки на платформу…",
    )

    try:
        await send_survey(payload)
    except Exception:
        logger.exception(
            "Не удалось отправить результаты опроса пользователя %s",
            payload.get("telegram_id"),
        )

        await state.set_state(SurveyStates.retry)
        await _edit_message(
            callback,
            "Не удалось отправить оценки. Попробуйте ещё раз.",
            get_retry_keyboard(),
        )
        return

    await state.clear()

    await _edit_message(
        callback,
        "Большое спасибо за участие в опросе! Ваши оценки отправлены.",
    )

    logger.info(
        "Пользователь %s завершил опрос",
        payload.get("telegram_id"),
    )


# ---------------------------------------------------------------------------
# Тестовая отправка предложения пройти опрос
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "survey:test:start")
async def start_test_survey_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    logger.info(
        "Нажата тестовая кнопка. Telegram ID: %s",
        callback.from_user.id,
    )

    if callback.from_user.id != TEST_TELEGRAM_ID:
        logger.warning("Тестовый опрос запущен неавторизованным пользователем")
        await _answer(
            callback,
            "Тестовый опрос недоступен.",
            show_alert=True,
        )
        return

    await _answer(callback)
    await _start_survey(callback, state, is_test=True)

    logger.info("Тестовый опрос успешно запущен")


# ---------------------------------------------------------------------------
# Начало опроса
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("survey:start"))
async def start_survey_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    # startswith нужен, чтобы старые кнопки survey:start:<id>
    # тоже открывали опрос после смены формата callback_data.
    await _answer(callback)
    await _start_survey(callback, state, is_test=False)


# ---------------------------------------------------------------------------
# Отказ от опроса
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "survey:decline")
async def decline_survey_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    current_state = await state.get_state()

    if current_state == SurveyStates.sending.state:
        await _answer(
            callback,
            "Опрос уже отправляется.",
            show_alert=True,
        )
        return

    await state.clear()
    await _answer(callback, "Вы отказались от прохождения опроса.")

    await _edit_message(
        callback,
        "Вы отказались от прохождения опроса.",
    )


# ---------------------------------------------------------------------------
# Обработка ответов
# ---------------------------------------------------------------------------

@router.callback_query(
    StateFilter(
        SurveyStates.question_1,
        SurveyStates.question_2,
        SurveyStates.question_3,
    ),
    F.data.startswith("survey:rate:"),
)
async def survey_rating_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    parts = callback.data.split(":")

    # Новый формат: survey:rate:<question>:<score>.
    # Старый survey:rate:<score> больше не принимаем: он не позволяет
    # отличить ответ на текущий вопрос от двойного клика по прошлому.
    if len(parts) != 4:
        await _answer(
            callback,
            "Кнопка устарела. Начните опрос заново.",
            show_alert=True,
        )
        return

    try:
        question_number = int(parts[2])
        score = int(parts[3])
    except ValueError:
        await _answer(callback, "Недопустимая оценка.", show_alert=True)
        return

    if question_number not in STATE_BY_QUESTION or score not in range(1, 6):
        await _answer(callback, "Недопустимая оценка.", show_alert=True)
        return

    current_state = await state.get_state()
    current_question = QUESTION_BY_STATE.get(current_state)

    if current_question is None:
        await _answer(
            callback,
            "Сессия опроса не найдена. Начните заново.",
            show_alert=True,
        )
        return

    if question_number != current_question:
        await _answer(
            callback,
            "Этот вопрос уже пройден.",
            show_alert=True,
        )
        return

    data = await state.get_data()
    answers = list(data.get("answers", []))

    if len(answers) != current_question - 1:
        logger.warning(
            "Некорректное состояние опроса пользователя %s: "
            "вопрос %s, ответов %s",
            callback.from_user.id,
            current_question,
            len(answers),
        )

        await state.clear()
        await _answer(
            callback,
            "Сессия опроса устарела. Начните заново.",
            show_alert=True,
        )
        await _edit_message(
            callback,
            "Сессия опроса устарела. Начните опрос заново.",
        )
        return

    answers.append(score)

    # Отвечаем на callback сразу, чтобы Telegram не показывал
    # бесконечную загрузку, пока идёт запрос в API.
    await _answer(callback)

    if current_question < 3:
        next_question = current_question + 1

        await state.update_data(answers=answers)
        await state.set_state(STATE_BY_QUESTION[next_question])

        await _edit_message(
            callback,
            SURVEY_QUESTIONS[next_question - 1],
            get_rating_keyboard(next_question),
        )
        return

    await state.update_data(answers=answers)

    if data.get("is_test"):
        await state.clear()
        await _edit_message(
            callback,
            "Тестовый опрос завершён. Ответы не сохранены.",
        )
        return

    payload = Survey(
        telegram_id=callback.from_user.id,
        question_1=answers[0],
        question_2=answers[1],
        question_3=answers[2],
    ).model_dump(mode="json")

    await state.update_data(payload=payload)
    await _submit_survey(callback, state, payload)


# ---------------------------------------------------------------------------
# Повторная отправка после ошибки API
# ---------------------------------------------------------------------------

@router.callback_query(
    StateFilter(SurveyStates.retry),
    F.data == "survey:retry",
)
async def retry_survey_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    payload = data.get("payload")

    if not payload:
        await state.clear()
        await _answer(
            callback,
            "Данные опроса потеряны. Начните заново.",
            show_alert=True,
        )
        await _edit_message(
            callback,
            "Данные опроса потеряны. Начните опрос заново.",
        )
        return

    await _answer(callback)
    await _submit_survey(callback, state, payload)
