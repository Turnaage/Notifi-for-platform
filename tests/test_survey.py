from keyboards.survey import (
    get_rating_keyboard,
    get_survey_invite_keyboard,
)
from schemas.survey_states import Survey


def test_survey_payload_uses_telegram_id():
    payload = Survey(
        telegram_id=123456789,
        question_1=5,
        question_2=4,
        question_3=3,
    ).model_dump(mode="json")

    assert payload["telegram_id"] == 123456789
    assert "user_id" not in payload
    assert payload["question_1"] == 5
    assert payload["question_2"] == 4
    assert payload["question_3"] == 3


def test_survey_invite_keyboard_has_no_curator_id():
    button = get_survey_invite_keyboard().inline_keyboard[0][0]

    assert button.callback_data == "survey:start"


def test_rating_keyboard_contains_question_number():
    button = get_rating_keyboard(2).inline_keyboard[0][0]

    assert button.callback_data == "survey:rate:2:1"
