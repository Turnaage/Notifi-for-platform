from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from core.config import logger
from keyboards.survey import get_survey_invite_keyboard

from database.db import get_users_for_survey


async def send_monthly_surveys(bot: Bot):
    """
    Ежемесячная рассылка предложений пройти опрос.
    """

    users = await get_users_for_survey()

    sent = 0
    failed = 0

    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    "📋 <b>Оценка работы куратора</b>\n\n"
                    "Пожалуйста, пройди небольшой опрос "
                    "и оцени работу своего куратора."
                ),
                reply_markup=get_survey_invite_keyboard(
                    user.curator_id
                ),
                parse_mode="HTML"
            )

            sent += 1

        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
            logger.exception(
                "Не удалось отправить опрос пользователю %s",
                user.telegram_id
            )

        except Exception:
            failed += 1
            logger.exception(
                "Ошибка отправки опроса пользователю %s",
                user.telegram_id
            )

    logger.info(
        "Ежемесячная рассылка опросов завершена. Отправлено: %s, ошибок: %s",
        sent,
        failed
    )