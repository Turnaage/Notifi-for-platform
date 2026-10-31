
from aiogram.types import Message
from core.config import router


@router.message()
async def unknown_message(message: Message):
    await message.answer(
        "Не понял твоё сообщение. Давай начнём сначала."
    )
    await message.answer(
        "Нажми /start, чтобы начать."
    )