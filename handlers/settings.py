
import logging

import aiohttp
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database.db import (
    ensure_user,
    get_user,
    set_reminders_enabled,
    set_reminder_interval_hours,
    set_reminder_schedule
)
from services.api import update_lesson_mode
from services.schedule import REMINDER_SCHEDULES

logger = logging.getLogger(__name__)

router = Router()

REMINDER_INTERVALS = (24, 48, 72, 168)

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
    reminders_enabled: bool,
    interval_hours: int,
):
    reminder_button = (
        "Выключить напоминания"
        if reminders_enabled
        else "Включить напоминания"
    )

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
                    text=f"Выбрать частоту уведомлений: {interval_hours} ч.",
                    callback_data="settings:frequency",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Выбрать расписание уведомлений",
                    callback_data="settings:schedule",
                )
            ]
        ]
    )


def get_frequency_keyboard(current_interval: int):
    buttons = []

    for hours in REMINDER_INTERVALS:
        label = f"{hours} часов"

        if hours == 168:
            label = "7 дней"

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


async def show_settings(message: Message):
    telegram_id = message.from_user.id

    logger.info(
        "Пользователь %s открыл настройки",
        telegram_id,
    )

    try:
        await ensure_user(telegram_id)
        user = await get_user(telegram_id)

        if user is None:
            logger.warning(
                "Не удалось найти настройки пользователя %s",
                telegram_id,
            )

            await message.answer(
                "Не удалось загрузить настройки. Попробуй позже."
            )
            return

        reminder_status = (
            "включены" if user.reminders_enabled else "выключены"
        )

        await message.answer(
            "Настройки обучения\n\n"
            f"Напоминания: {reminder_status}\n"
            f"Частота напоминаний: каждые "
            f"{user.reminder_interval_hours} ч.\n\n"
            "Уроки по порядку - уведомления об уроках, по общему порядку\n"
            "Уроки в зависимости от последнего - Уроки по порядку того модуля, последний урок которого вы отправили",
            reply_markup=get_settings_keyboard(
                user.reminders_enabled,
                user.reminder_interval_hours,
            ),
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
        user = await get_user(telegram_id)

        if user is None:
            await callback.answer(
                "Не удалось загрузить настройки.",
                show_alert=True,
            )
            return

        await callback.answer()

        if callback.message:
            await callback.message.answer(
                "Выбери, как часто отправлять тебе напоминания:",
                reply_markup=get_frequency_keyboard(
                    user.reminder_interval_hours
                ),
            )

        logger.info(
            "Пользователь %s открыл выбор частоты напоминаний",
            telegram_id,
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


@router.callback_query(
    F.data.startswith("settings:interval:")
)
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

        logger.info(
            "Пользователь %s установил частоту напоминаний: %s часов",
            telegram_id,
            interval_hours,
        )

        await callback.answer(
            f"Частота установлена: {interval_hours} ч."
        )

        if callback.message:
            await callback.message.answer(
                f"Частота напоминаний изменена: "
                f"{interval_hours} ч.",
                reply_markup=get_frequency_keyboard(
                    interval_hours
                ),
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
        user = await get_user(telegram_id)

        if user is None:
            await callback.answer(
                "Не удалось загрузить настройки.",
                show_alert=True,
            )
            return

        await callback.answer()

        if callback.message:
            reminder_status = (
                "включены"
                if user.reminders_enabled
                else "выключены"
            )

            await callback.message.answer(
                "Настройки обучения\n\n"
                f"Напоминания: {reminder_status}\n"
                f"Частота напоминаний: "
                f"{user.reminder_interval_hours} ч.\n\n"
                "Выбери режим получения следующего урока:",
                reply_markup=get_settings_keyboard(
                    user.reminders_enabled,
                    user.reminder_interval_hours,
                ),
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

    logger.info(
        "Пользователь %s меняет режим уроков на %s",
        telegram_id,
        mode,
    )

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
        await ensure_user(telegram_id)
        user = await get_user(telegram_id)

        if user is None:
            await callback.answer(
                "Не удалось загрузить настройки.",
                show_alert=True,
            )
            return

        new_value = not user.reminders_enabled

        await set_reminders_enabled(telegram_id, new_value)

        status = "включены" if new_value else "выключены"

        await callback.answer(
            f"Напоминания {status}."
        )

        updated_user = await get_user(telegram_id)

        if callback.message and updated_user:
            await callback.message.answer(
                f"Напоминания {status}.",
                reply_markup=get_settings_keyboard(
                    updated_user.reminders_enabled,
                    updated_user.reminder_interval_hours,
                ),
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

@router.callback_query(
    F.data == "settings:schedule"
)
async def schedule_settings_handler(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)

    if user is None:
        await callback.answer(
            "Пользователь не найден",
            show_alert=True,
        )
        return

    keyboard = get_schedule_keyboard(
        user.reminder_schedule
    )

    await callback.message.edit_text(
        "Настройки уведомлений",
        reply_markup=get_settings_keyboard(
            reminders_enabled=user.reminders_enabled,
            interval_hours=user.reminder_interval_hours,
        ),
    )

    await callback.message.edit_text(
        "Выбери расписание уведомлений:\n\n"
        "После работы — будни 18:00–22:00, "
        "выходные 10:00–20:00.\n\n"
        "Утреннее — будни 07:00–09:00, "
        "выходные 09:00–12:00.\n\n"
        "Вечернее — будни и выходные 18:00–22:00.",
        reply_markup=keyboard,
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("settings:schedule:")
)
async def set_schedule_handler(callback: CallbackQuery):
    schedule_name = callback.data.split(":")[-1]

    if schedule_name not in REMINDER_SCHEDULES:
        await callback.answer(
            "Неизвестное расписание",
            show_alert=True,
        )
        return

    try:
        await set_reminder_schedule(
            callback.from_user.id,
            schedule_name,
        )

    except Exception:
        logger.exception(
            "Не удалось изменить расписание пользователя %s",
            callback.from_user.id,
        )

        await callback.answer(
            "Не удалось сохранить расписание",
            show_alert=True,
        )
        return

    await callback.answer("Расписание сохранено")

    user = await get_user(callback.from_user.id)

    await callback.message.edit_text(
        "Настройки уведомлений",
        reply_markup=get_settings_keyboard(
            reminders_enabled=user.reminders_enabled,
            interval_hours=user.reminder_interval_hours,
            # Если твоя клавиатура принимает другие параметры,
            # сохрани существующий вызов и добавь расписание отдельно.
        ),
    )