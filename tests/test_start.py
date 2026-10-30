
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from handlers import start


@pytest.mark.asyncio
async def test_start_handler_registers_user_and_sends_welcome(monkeypatch):
    telegram_id = 123456789

    ensure_user_mock = AsyncMock()
    monkeypatch.setattr(start, "ensure_user", ensure_user_mock)

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=telegram_id),
        answer=AsyncMock(),
    )

    await start.start_handler(message)

    ensure_user_mock.assert_awaited_once_with(telegram_id)

    message.answer.assert_awaited_once()

    args = message.answer.await_args
    text = args.args[0]

    assert "Привет!" in text
    assert "Выбери действие:" in text

    keyboard = args.kwargs["reply_markup"]
    buttons = [
        button.text
        for row in keyboard.keyboard
        for button in row
    ]

    assert buttons == ["Следующий урок", "Настройки"]
