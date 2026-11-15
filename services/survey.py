import asyncio

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)

from core.config import logger, TEST_TELEGRAM_ID
from database.db import get_users_for_survey
from keyboards.survey import (
    get_survey_invite_keyboard,
    get_test_survey_invite_keyboard,
)


TELEGRAM_SEND_ATTEMPTS = 3
TELEGRAM_RETRY_BASE_DELAY = 1.0
SEND_DELAY_SECONDS = 0.05


async def send_test_survey(bot: Bot):
    if not TEST_TELEGRAM_ID:
        raise ValueError("TEST_TELEGRAM_ID не указан в .env")

    await bot.send_message(
        chat_id=TEST_TELEGRAM_ID,
        text=(
            "📋 <b>Тестовый опрос</b>\n\n"
            "Нажми кнопку ниже, чтобы пройти опрос."
        ),
        reply_markup=get_test_survey_invite_keyboard(),
        parse_mode="HTML",
    )


async def _send_survey_invite(bot: Bot, telegram_id: int) -> None:
    """Отправить приглашение с повторами при временных ошибках Telegram."""
    for attempt in range(1, TELEGRAM_SEND_ATTEMPTS + 1):
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    "📋 <b>Оценка работы куратора</b>\n\n"
                    "Пожалуйста, пройди небольшой опрос "
                    "и оцени работу своего куратора."
                ),
                reply_markup=get_survey_invite_keyboard(),
                parse_mode="HTML",
            )
            return

        except TelegramRetryAfter as error:
            if attempt >= TELEGRAM_SEND_ATTEMPTS:
                raise

            logger.warning(
                "Telegram попросил подождать %s сек. перед отправкой "
                "пользователю %s (попытка %s/%s)",
                error.retry_after,
                telegram_id,
                attempt,
                TELEGRAM_SEND_ATTEMPTS,
            )
            await asyncio.sleep(error.retry_after)

        except (
            TelegramForbiddenError,
            TelegramBadRequest,
            TelegramUnauthorizedError,
        ):
            # Повторять бессмысленно: бот заблокирован, чат не найден,
            # токен неверный и т.п.
            raise

        except (TelegramAPIError, asyncio.TimeoutError) as error:
            if attempt >= TELEGRAM_SEND_ATTEMPTS:
                raise

            delay = TELEGRAM_RETRY_BASE_DELAY * attempt
            logger.warning(
                "Ошибка Telegram при отправке пользователю %s "
                "(попытка %s/%s): %s. Повтор через %s сек.",
                telegram_id,
                attempt,
                TELEGRAM_SEND_ATTEMPTS,
                error,
                delay,
            )
            await asyncio.sleep(delay)


async def send_monthly_surveys(bot: Bot) -> dict[str, int]:
    """
    Ежемесячная рассылка предложений пройти опрос.
    """
    users = await get_users_for_survey()

    sent = 0
    failed = 0

    if not users:
        logger.warning("Нет пользователей для ежемесячного опроса")

    for telegram_id in users:
        try:
            await _send_survey_invite(bot, telegram_id)
            sent += 1

        except (
            TelegramForbiddenError,
            TelegramBadRequest,
            TelegramUnauthorizedError,
        ):
            failed += 1
            logger.exception(
                "Не удалось отправить опрос пользователю %s",
                telegram_id,
            )

        except Exception:
            failed += 1
            logger.exception(
                "Ошибка отправки опроса пользователю %s",
                telegram_id,
            )

        await asyncio.sleep(SEND_DELAY_SECONDS)

    logger.info(
        "Ежемесячная рассылка завершена. "
        "Всего: %s, отправлено: %s, ошибок: %s",
        len(users),
        sent,
        failed,
    )

    return {
        "total": len(users),
        "sent": sent,
        "failed": failed,
    }
