
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from handlers import settings


@pytest.mark.asyncio
async def test_settings_handler_answers_user():
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=123456789),
        answer=AsyncMock(),
    )

    await settings.settings_handler(message)

    message.answer.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode", ["course_order", "last_completed"]
)
async def test_lesson_mode_is_sent_to_api(monkeypatch, mode):
    update_lesson_mode = AsyncMock(
        return_value={"success": True}
    )
    monkeypatch.setattr(
        settings, "update_lesson_mode", update_lesson_mode
    )

    callback = SimpleNamespace(
        from_user=SimpleNamespace(id=123456789),
        data=f"lesson_mode:{mode}",
        answer=AsyncMock(),
        message=SimpleNamespace(answer=AsyncMock()),
    )

    await settings.lesson_mode_handler(callback)

    update_lesson_mode.assert_awaited_once_with(
        123456789, mode
    )
    callback.answer.assert_awaited_once()
