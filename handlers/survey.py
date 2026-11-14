from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from core.config import router, logger, TEST_TELEGRAM_ID

from keyboards.survey import (
    get_survey_invite_keyboard,
    get_rating_keyboard
)

from schemas.survey_states import SurveyStates

from database.db import (
    save_survey,
    update_curator_states
)

# ---------------------------------------------------------------------------
# Тестовая отправка предложения пройти опрос
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "survey:test:start")
async def start_test_survey_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    logger.info(
        "Нажата тестовая кнопка. Telegram ID: %s",
        callback.from_user.id
    )

    await callback.answer()

    if callback.from_user.id != TEST_TELEGRAM_ID:
        logger.warning("Тестовый опрос запущен неавторизованным пользователем")
        if callback.message:
            await callback.message.answer(
                "Тестовый опрос недоступен."
            )
        return

    await state.update_data(
        curator_id=0,
        answers=[],
        is_test=True
    )

    await state.set_state(SurveyStates.question_1)

    if callback.message:
        await callback.message.edit_text(
            "1. Насколько вы довольны работой куратора?",
            reply_markup=get_rating_keyboard()
        )

    logger.info("Тестовый опрос успешно запущен")


# ---------------------------------------------------------------------------
# Отправка предложения пройти опрос
# ---------------------------------------------------------------------------

async def send_survey_invite(
    message: Message,
    curator_id: int
):
    await message.answer(
        "📋 <b>Оценка работы куратора</b>\n\n"
        "Пожалуйста, пройди небольшой опрос и оцени работу своего куратора.",
        reply_markup=get_survey_invite_keyboard(curator_id),
        parse_mode="HTML"
    )


# ---------------------------------------------------------------------------
# Начало опроса
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("survey:start:"))
async def start_survey_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    curator_id = int(callback.data.rsplit(":", maxsplit=1)[-1])

    await state.update_data(
        curator_id=curator_id,
        answers=[],
        is_test=False
    )

    await state.set_state(SurveyStates.question_1)

    await callback.answer()

    if callback.message:
        await callback.message.edit_text(
            "1. Насколько вы довольны работой куратора?",
            reply_markup=get_rating_keyboard()
        )


# ---------------------------------------------------------------------------
# Отказ от опроса
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "survey:decline")
async def decline_survey_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.clear()
    await callback.answer("Вы отказались от прохождения опроса.")

    if callback.message:
        await callback.message.edit_text(
            "Вы отказались от прохождения опроса."
        )


# ---------------------------------------------------------------------------
# Обработка ответов
# ---------------------------------------------------------------------------

@router.callback_query(
    StateFilter(
        SurveyStates.question_1,
        SurveyStates.question_2,
        SurveyStates.question_3
    ),
    F.data.startswith("survey:rate:")
)
async def survey_rating_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    score = int(callback.data.rsplit(":", maxsplit=1)[-1])

    if score not in range(1, 6):
        await callback.answer("Недопустимая оценка.", show_alert=True)
        return

    data = await state.get_data()
    answers = data["answers"]

    answers.append(score)

    await state.update_data(answers=answers)

    current_state = await state.get_state()

    if current_state == SurveyStates.question_1.state:
        await state.set_state(SurveyStates.question_2)

        question = (
            "2. Насколько куратор помогал вам в обучении?"
        )

    elif current_state == SurveyStates.question_2.state:
        await state.set_state(SurveyStates.question_3)

        question = (
            "3. Насколько вы довольны коммуникацией с куратором?"
        )

    else:
        curator_id = data["curator_id"]
        user_id = callback.from_user.id

        if data.get("is_test"):
            await state.clear()
            await callback.answer("Тестовый опрос завершён.")

            if callback.message:
                await callback.message.edit_text(
                    "Тестовый опрос завершён. Ответы не сохранены."
                )

            return

        await save_survey(
            curator_id=curator_id,
            user_id=user_id,
            answers=answers
        )

        await update_curator_states(curator_id)

        await state.clear()

        await callback.answer("Опрос завершён.")

        if callback.message:
            await callback.message.edit_text(
                "Большое спасибо за участие в опросе! Ваши оценки сохранены."
            )

        logger.info(
            "Пользователь %s завершил опрос куратора %s",
            user_id,
            curator_id
        )

        return

    await callback.answer()

    if callback.message:
        await callback.message.edit_text(
            question,
            reply_markup=get_rating_keyboard()
        )