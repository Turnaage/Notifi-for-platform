
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from services import api


def setup_http_mock(monkeypatch, status=200, payload=None):
    """Подменяет HTTP-сессию, не отправляя реальных запросов."""

    response = MagicMock()
    response.status = status
    response.raise_for_status = MagicMock()

    if status >= 400:
        response.raise_for_status.side_effect = (
            aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=status,
                message="HTTP error",
            )
        )

    response.json = AsyncMock(return_value=payload)

    request_context = MagicMock()
    request_context.__aenter__ = AsyncMock(return_value=response)
    request_context.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get.return_value = request_context

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(
        api.aiohttp,
        "ClientSession",
        MagicMock(return_value=session_context),
    )

    return session


@pytest.mark.asyncio
async def test_get_progress_mock():
    telegram_id = 2121892985

    result = await api.get_progress(telegram_id)

    assert result == {
        "user_id": telegram_id,
        "progress": 65,
        "status": "in_progress",
    }


@pytest.mark.asyncio
async def test_get_progress_http_success(monkeypatch):
    monkeypatch.setattr(api, "MOCK_API", False)

    telegram_id = 2121892985
    expected_data = {
        "last_activity_at": "2026-10-27T10:00:00Z",
        "has_pending_review": False,
    }

    session = setup_http_mock(
        monkeypatch,
        status=200,
        payload=expected_data,
    )

    result = await api.get_progress(telegram_id)

    assert result == expected_data
    session.get.assert_called_once_with(
        f"{api.API_BASE_URL}/progress",
        params={"telegram_id": telegram_id},
    )


@pytest.mark.asyncio
async def test_get_progress_http_error(monkeypatch):
    monkeypatch.setattr(api, "MOCK_API", False)

    telegram_id = 2121892985

    setup_http_mock(
        monkeypatch,
        status=500,
        payload={"error": "Internal Server Error"},
    )

    with pytest.raises(aiohttp.ClientResponseError) as error:
        await api.get_progress(telegram_id)

    assert error.value.status == 500
