from datetime import datetime, timezone

from aiogram.fsm.state import State, StatesGroup
from pydantic import BaseModel, Field


class SurveyStates(StatesGroup):
    question_1 = State()
    question_2 = State()
    question_3 = State()
    sending = State()
    retry = State()


class Survey(BaseModel):
    telegram_id: int

    question_1: int = Field(ge=1, le=5)
    question_2: int = Field(ge=1, le=5)
    question_3: int = Field(ge=1, le=5)

    sent_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
