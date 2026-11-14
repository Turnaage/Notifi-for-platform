from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import REMINDER_SCHEDULES, REMINDER_INTERVALS
from schemas.user_settings import UserSettings


def get_schedule_keyboard(current_schedule: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for schedule_id, schedule in REMINDER_SCHEDULES.items():
        mark = " ✓" if schedule_id == current_schedule else ""

        builder.button(
            text=f"{schedule['name']}{mark}",
            callback_data=f"settings:schedule:{schedule_id}",
        )

    builder.button(
        text="← Назад к настройкам",
        callback_data="settings:back",
    )
    builder.button(
        text="🏠 На главный экран",
        callback_data="settings:main",
    )
    builder.adjust(1)

    return builder.as_markup()


def get_settings_keyboard(settings: UserSettings) -> InlineKeyboardMarkup:
    reminder_button = (
        "⏸ Приостановить напоминания"
        if settings.reminders_enabled
        else "▶️ Возобновить напоминания"
    )

    schedule_name = REMINDER_SCHEDULES[
        settings.reminder_schedule
    ]["name"]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📚 Последовательный режим",
                    callback_data="settings:mode:course_order",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Адаптивный режим",
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
                        "⏱ Частота напоминаний: "
                        f"{settings.reminder_interval_hours} ч."
                    ),
                    callback_data="settings:frequency",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🗓 Расписание: {schedule_name}",
                    callback_data="settings:schedule",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 На главный экран",
                    callback_data="settings:main",
                )
            ],
        ]
    )


def get_frequency_keyboard(current_interval: int) -> InlineKeyboardMarkup:
    buttons = []

    for hours in REMINDER_INTERVALS:
        label = "7 дней" if hours == 168 else f"{hours} ч."

        if hours == current_interval:
            label = f"✓ {label}"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"settings:interval:{hours}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="← Назад к настройкам",
                callback_data="settings:back",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 На главный экран",
                callback_data="settings:main",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

