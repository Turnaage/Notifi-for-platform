

import aiohttp

from core.config import API_BASE_URL, API_TOKEN, logger


TIMEOUT = aiohttp.ClientTimeout(total=15)

MOCK_API = False


def get_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json",
    }

    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"

    return headers


async def get_next_lesson(telegram_id: int) -> dict | None:
    logger.info(
        "Запрос следующего урока для пользователя %s",
        telegram_id,
    )

    try:
        async with aiohttp.ClientSession(
            headers=get_headers(),
            timeout=TIMEOUT,
        ) as session:
            async with session.get(
                f"{API_BASE_URL}/next-lesson",
                params={"telegram_id": telegram_id},
            ) as response:
                response.raise_for_status()
                data = await response.json()

        lesson = data.get("lesson")

        logger.info(
            "Получен ответ API по следующему уроку для пользователя %s",
            telegram_id,
        )

        return lesson

    except Exception:
        logger.exception(
            "Ошибка получения следующего урока для пользователя %s",
            telegram_id,
        )
        raise


async def get_progress(telegram_id: int) -> dict:
    logger.info(
        "Запрос прогресса пользователя %s",
        telegram_id,
    )

    if MOCK_API:
        logger.info(
            "Используются тестовые данные прогресса для пользователя %s",
            telegram_id,
        )

        return {
            "user_id": telegram_id,
            "progress": 65,
            "status": "in_progress",
        }

    try:
        async with aiohttp.ClientSession(
            headers=get_headers(),
            timeout=TIMEOUT,
        ) as session:
            async with session.get(
                f"{API_BASE_URL}/progress",
                params={"telegram_id": telegram_id},
            ) as response:
                response.raise_for_status()
                data = await response.json()

        logger.info(
            "Прогресс пользователя %s получен",
            telegram_id,
        )

        return data

    except Exception:
        logger.exception(
            "Ошибка получения прогресса пользователя %s",
            telegram_id,
        )
        raise


async def update_lesson_mode(
    telegram_id: int,
    mode: str,
) -> dict:
    allowed_modes = {
        "course_order",
        "last_completed",
    }

    if mode not in allowed_modes:
        logger.warning(
            "Передан неизвестный режим урока: %s",
            mode,
        )
        raise ValueError(f"Неизвестный режим урока: {mode}")

    logger.info(
        "Изменение режима уроков пользователя %s: %s",
        telegram_id,
        mode,
    )

    try:
        async with aiohttp.ClientSession(
            headers=get_headers(),
            timeout=TIMEOUT,
        ) as session:
            async with session.patch(
                f"{API_BASE_URL}/settings",
                json={
                    "telegram_id": telegram_id,
                    "next_lesson_mode": mode,
                },
            ) as response:
                response.raise_for_status()

                if response.status == 204:
                    data = {"success": True}
                else:
                    data = await response.json()

        logger.info(
            "Режим уроков пользователя %s успешно обновлён",
            telegram_id,
        )

        return data

    except Exception:
        logger.exception(
            "Ошибка изменения режима уроков пользователя %s",
            telegram_id,
        )
        raise
