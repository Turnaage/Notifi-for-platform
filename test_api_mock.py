import asyncio
from unittest.mock import AsyncMock, patch


async def main():
    fake_lesson = {
        "name": "Тестовый урок по Python",
        "url": "https://example.com/lesson/1",
    }

    fake_progress = {
        "last_activity_at": "2026-10-25T10:00:00Z",
        "has_pending_review": False,
    }

    with (
        patch(
            "services.reminders.get_next_lesson",
            new_callable=AsyncMock,
            return_value=fake_lesson,
        ),
        patch(
            "services.reminders.get_progress",
            new_callable=AsyncMock,
            return_value=fake_progress,
        ),
    ):
        from services.api import get_next_lesson as mocked_lesson
        from services.api import get_progress as mocked_progress

        lesson = await mocked_lesson(123456789)
        progress = await mocked_progress(123456789)

        print("Тестовый урок:", lesson)
        print("Тестовый прогресс:", progress)


if __name__ == "__main__":
    asyncio.run(main())