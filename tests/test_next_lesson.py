
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from handlers import next_lesson


@pytest.mark.asyncio
async def test_next_lesson_sends_lesson_details(monkeypatch):
    lesson = {
        "name": "Урок 1",
        "url": "https://example.com/lesson/1",
    }
    get_next_lesson = AsyncMock(return_value=lesson)
    monkeypatch.setattr(next_lesson, "get_next_lesson", get_next_lesson)

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=123456789),
        answer=AsyncMock(),
    )

    await next_lesson.next_lesson_handler(message)

    get_next_lesson.assert_awaited_once_with(123456789)
    message.answer.assert_awaited_once()

    sent_text = message.answer.await_args.args[0]
    assert lesson["name"] in sent_text
    assert lesson["url"] in sent_text


@pytest.mark.asyncio
async def test_next_lesson_handles_no_available_lesson(monkeypatch):
    get_next_lesson = AsyncMock(return_value=None)
    monkeypatch.setattr(next_lesson, "get_next_lesson", get_next_lesson)

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=123456789),
        answer=AsyncMock(),
    )

    await next_lesson.next_lesson_handler(message)

    get_next_lesson.assert_awaited_once_with(123456789)
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_next_lesson_handles_api_failure(monkeypatch):
    monkeypatch.setattr(
        next_lesson,
        "get_next_lesson",
        AsyncMock(side_effect=RuntimeError("API unavailable")),
    )

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=123456789),
        answer=AsyncMock(),
    )

    await next_lesson.next_lesson_handler(message)

    message.answer.assert_awaited_once()
