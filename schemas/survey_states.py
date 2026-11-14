from aiogram.fsm.state import State, StatesGroup


class SurveyStates(StatesGroup):
    question_1 = State()
    question_2 = State()
    question_3 = State()