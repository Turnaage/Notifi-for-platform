
import aiohttp
from aiogram import F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    ensure_user,
    get_user,
    set_reminders_enabled,
    set_reminder_interval_hours,
    set_reminder_schedule,
)
from schemas.user_settings import UserSettings
from services.api import update_lesson_mode
from services.schedule import REMINDER_SCHEDULES
from core.config import logger, router, REMINDER_INTERVALS



async def get_user_settings(telegram_id: int) -> UserSettings | None:
    """Получает и валидирует настройки пользователя."""
    await ensure_user(telegram_id)

    user = await get_user(telegram_id)

    if user is None:
        return None

    return UserSettings.model_validate(user)


def get_schedule_keyboard(current_schedule: str):
    builder = InlineKeyboardBuilder()

    for schedule_id, schedule in REMINDER_SCHEDULES.items():
        mark = " ✓" if schedule_id == current_schedule else ""

        builder.button(
            text=f"{schedule['name']}{mark}",
            callback_data=f"settings:schedule:{schedule_id}",
        )

    builder.button(
        text="Назад",
        callback_data="settings:back",
    )

    builder.adjust(1)

    return builder.as_markup()


def get_settings_keyboard(
    settings: UserSettings,
) -> InlineKeyboardMarkup:
    reminder_button = (
        "Выключить напоминания"
        if settings.reminders_enabled
        else "Включить напоминания"
    )

    schedule_name = REMINDER_SCHEDULES[
        settings.reminder_schedule
    ]["name"]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Уроки по порядку",
                    callback_data="settings:mode:course_order",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Уроки в зависимости от последнего",
                    callback_data="settings:mode:last_completed",
                )
            ],
            [
                InlineKeyboardButton(
                    text=reminder_button,
                    callback_data="settings:toggle_reminders",
                )
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "Выбрать частоту уведомлений: "
                        f"{settings.reminder_interval_hours} ч."
                    ),
                    callback_data="settings:frequency",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Расписание: {schedule_name}",
                    callback_data="settings:schedule",
                )
            ],
        ]
    )


def get_frequency_keyboard(
    current_interval: int,
) -> InlineKeyboardMarkup:
    buttons = []

    for hours in REMINDER_INTERVALS:
        label = "7 дней" if hours == 168 else f"{hours} часов"

        if hours == current_interval:
            label = f"✓ {label}"

        buttons.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"settings:interval:{hours}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="Назад к настройкам",
            callback_data="settings:back",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_text(settings: UserSettings) -> str:
    reminder_status = (
        "включены"
        if settings.reminders_enabled
        else "выключены"
    )

    schedule_name = REMINDER_SCHEDULES[
        settings.reminder_schedule
    ]["name"]

    return (
        "Настройки обучения\n\n"
        f"Напоминания: {reminder_status}\n"
        f"Частота напоминаний: каждые "
        f"{settings.reminder_interval_hours} ч.\n"
        f"Расписание: {schedule_name}\n\n"
        "Уроки по порядку — уведомления об уроках "
        "в общем порядке.\n"
        "Уроки в зависимости от последнего — "
        "уроки с учётом последнего завершённого урока."
    )


async def show_settings(message: Message):
    telegram_id = message.from_user.id

    logger.info(
        "Пользователь %s открыл настройки",
        telegram_id,
    )

    try:
        settings = await get_user_settings(telegram_id)

        if settings is None:
            await message.answer(
                "Не удалось загрузить настройки. Попробуй позже."
            )
            return

        await message.answer(
            get_settings_text(settings),
            reply_markup=get_settings_keyboard(settings),
        )

        logger.info(
            "Настройки пользователя %s успешно отображены",
            telegram_id,
        )

    except Exception:
        logger.exception(
            "Ошибка отображения настроек пользователя %s",
            telegram_id,
        )
        raise


@router.message(Command("settings"))
@router.message(F.text == "Настройки")
async def settings_handler(message: Message):
    await show_settings(message)


@router.callback_query(F.data == "settings:frequency")
async def frequency_settings_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id

    try:
        settings = await get_user_settings(telegram_id)

        if settings is None:
            await callback.answer(
                "Не удалось загрузить настройки.",
                show_alert=True,
            )
            return

        await callback.answer()

        if callback.message:
            await callback.message.edit_text(
                "Выбери, как часто отправлять тебе напоминания:",
                reply_markup=get_frequency_keyboard(
                    settings.reminder_interval_hours
                ),
            )

    except Exception:
        logger.exception(
            "Ошибка открытия частоты напоминаний пользователя %s",
            telegram_id,
        )

        await callback.answer(
            "Не удалось загрузить настройки.",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("settings:interval:"))
async def set_frequency_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id

    try:
        interval_hours = int(
            callback.data.rsplit(":", maxsplit=1)[-1]
        )

        if interval_hours not in REMINDER_INTERVALS:
            await callback.answer(
                "Недопустимая частота уведомлений.",
                show_alert=True,
            )
            return

        await set_reminder_interval_hours(
            telegram_id,
            interval_hours,
        )

        settings = await get_user_settings(telegram_id)

        if settings is None:
            await callback.answer(
                "Не удалось загрузить настройки.",
                show_alert=True,
            )
            return

        await callback.answer(
            f"Частота установлена: {interval_hours} ч."
        )

        if callback.message:
            await callback.message.edit_text(
                get_settings_text(settings),
                reply_markup=get_settings_keyboard(settings),
            )

    except Exception:
        logger.exception(
            "Ошибка изменения частоты напоминаний пользователя %s",
            telegram_id,
        )

        await callback.answer(
            "Не удалось изменить частоту напоминаний.",
            show_alert=True,
        )


@router.callback_query(F.data == "settings:back")
async def settings_back_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id

    try:
        settings = await get_user_settings(telegram_id)

        if settings is None:
            await callback.answer(
                "Не удалось загрузить настройки.",
                show_alert=True,
            )
            return

        await callback.answer()

        if callback.message:
            await callback.message.edit_text(
                get_settings_text(settings),
                reply_markup=get_settings_keyboard(settings),
            )

    except Exception:
        logger.exception(
            "Ошибка возврата к настройкам пользователя %s",
            telegram_id,
        )

        await callback.answer(
            "Не удалось загрузить настройки.",
            show_alert=True,
        )


@router.callback_query(
    F.data.in_(
        {
            "settings:mode:course_order",
            "settings:mode:last_completed",
        }
    )
)
async def lesson_mode_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    mode = callback.data.rsplit(":", maxsplit=1)[-1]

    try:
        await update_lesson_mode(telegram_id, mode)

        mode_name = (
            "по порядку"
            if mode == "course_order"
            else "с учётом последнего завершённого урока"
        )

        await callback.answer("Режим обновлён.")

        if callback.message:
            await callback.message.answer(
                f"Режим следующего урока изменён: {mode_name}."
            )

        logger.info(
            "Режим уроков пользователя %s изменён на %s",
            telegram_id,
            mode,
        )

    except (aiohttp.ClientError, TimeoutError):
        logger.exception(
            "Ошибка обновления режима урока для пользователя %s",
            telegram_id,
        )

        await callback.answer(
            "Не удалось связаться с платформой.",
            show_alert=True,
        )

    except Exception:
        logger.exception(
            "Ошибка настройки режима урока для пользователя %s",
            telegram_id,
        )

        await callback.answer(
            "Не удалось изменить режим.",
            show_alert=True,
        )


@router.callback_query(F.data == "settings:toggle_reminders")
async def toggle_reminders_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id

    try:
        settings = await get_user_settings(telegram_id)

        if settings is None:
            await callback.answer(
                "Не удалось загрузить настройки.",
                show_alert=True,
            )
            return

        new_value = not settings.reminders_enabled

        await set_reminders_enabled(
            telegram_id,
            new_value,
        )

        updated_settings = await get_user_settings(telegram_id)

        if updated_settings is None:
            await callback.answer(
                "Настройки обновлены, но не удалось их загрузить.",
                show_alert=True,
            )
            return

        status = "включены" if new_value else "выключены"

        await callback.answer(
            f"Напоминания {status}."
        )

        if callback.message:
            await callback.message.edit_text(
                get_settings_text(updated_settings),
                reply_markup=get_settings_keyboard(updated_settings),
            )

        logger.info(
            "Пользователь %s изменил состояние напоминаний: %s",
            telegram_id,
            status,
        )

    except Exception:
        logger.exception(
            "Ошибка переключения напоминаний для пользователя %s",
            telegram_id,
        )

        await callback.answer(
            "Не удалось изменить настройки.",
            show_alert=True,
        )


@router.callback_query(F.data == "settings:schedule")
async def schedule_settings_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id

    try:
        settings = await get_user_settings(telegram_id)

        if settings is None:
            await callback.answer(
                "Пользователь не найден.",
                show_alert=True,
            )
            return

        if callback.message:
            await callback.message.edit_text(
                "Выбери расписание уведомлений:\n\n"
                "После работы — будни 18:00–22:00, "
                "выходные 10:00–20:00.\n\n"
                "Утреннее — будни 07:00–09:00, "
                "выходные 09:00–12:00.\n\n"
                "Вечернее — будни и выходные 18:00–22:00.",
                reply_markup=get_schedule_keyboard(
                    settings.reminder_schedule
                ),
            )

        await callback.answer()

    except Exception:
        logger.exception(
            "Ошибка открытия расписания пользователя %s",
            telegram_id,
        )

        await callback.answer(
            "Не удалось загрузить расписание.",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("settings:schedule:"))
async def set_schedule_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    schedule_name = callback.data.rsplit(":", maxsplit=1)[-1]

    if schedule_name not in REMINDER_SCHEDULES:
        await callback.answer(
            "Неизвестное расписание.",
            show_alert=True,
        )
        return

    try:
        await set_reminder_schedule(
            telegram_id,
            schedule_name,
        )

        settings = await get_user_settings(telegram_id)

        if settings is None:
            await callback.answer(
                "Расписание сохранено, но настройки не удалось загрузить.",
                show_alert=True,
            )
            return

        await callback.answer("Расписание сохранено.")

        if callback.message:
            await callback.message.edit_text(
                get_settings_text(settings),
                reply_markup=get_settings_keyboard(settings),
            )

        logger.info(
            "Пользователь %s установил расписание: %s",
            telegram_id,
            schedule_name,
        )

    except Exception:
        logger.exception(
            "Не удалось изменить расписание пользователя %s",
            telegram_id,
        )

        await callback.answer(
            "Не удалось сохранить расписание.",
            show_alert=True,
        )
