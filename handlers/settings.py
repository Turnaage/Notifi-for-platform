import aiohttp

from aiogram import F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from schemas.user_settings import UserSettings
from services.api import update_lesson_mode
from services.schedule import REMINDER_SCHEDULES
from database.db import (
    ensure_user,
    get_user,
    set_reminders_enabled,
    set_reminder_interval_hours,
    set_reminder_schedule,
)
from handlers.start import main_keyboard
from core.config import (
    logger,
    router,
    REMINDER_INTERVALS,
)


# ---------------------------------------------------------------------------
# Загрузка настроек
# ---------------------------------------------------------------------------

async def get_user_settings(telegram_id: int) -> UserSettings | None:
    """Получает и валидирует настройки пользователя."""
    await ensure_user(telegram_id)

    user = await get_user(telegram_id)

    if user is None:
        return None

    return UserSettings.model_validate(user.settings)


# ---------------------------------------------------------------------------
# Клавиатуры
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Тексты экранов
# ---------------------------------------------------------------------------

def get_settings_text(settings: UserSettings) -> str:
    reminder_status = (
        "активны"
        if settings.reminders_enabled
        else "приостановлены"
    )

    schedule_name = REMINDER_SCHEDULES[
        settings.reminder_schedule
    ]["name"]

    return (
        "⚙️ <b>Настройки обучения</b>\n\n"
        f"🔔 Напоминания: <b>{reminder_status}</b>\n"
        f"⏱ Частота: <b>каждые {settings.reminder_interval_hours} ч.</b>\n"
        f"🗓 Расписание: <b>{schedule_name}</b>\n\n"
        "📚 <b>Режим прохождения уроков</b>\n"
        "• <b>Последовательный</b> — бот предлагает уроки "
        "по порядку программы.\n"
        "• <b>Адаптивный</b> — бот учитывает твой прогресс "
        "на учебной платформе и предлагает следующий урок "
        "после последнего завершённого.\n\n"
        "Выбери нужный параметр ниже:"
    )


def get_schedule_text() -> str:
    return (
        "🗓 <b>Расписание напоминаний</b>\n\n"
        "Выбери время, в которое тебе удобнее получать напоминания:\n\n"
        "• <b>После работы</b> — будни 18:00–22:00, "
        "выходные 10:00–20:00.\n"
        "• <b>Утреннее</b> — будни 07:00–09:00, "
        "выходные 09:00–12:00.\n"
        "• <b>Вечернее</b> — каждый день 18:00–22:00."
    )


# ---------------------------------------------------------------------------
# Открытие настроек
# ---------------------------------------------------------------------------

async def show_settings(message: Message):
    telegram_id = message.from_user.id
    logger.info("Пользователь %s открыл настройки", telegram_id)

    settings = await get_user_settings(telegram_id)
    if settings is None:
        await message.answer("Не удалось загрузить настройки. Попробуй позже.")
        return

    await message.answer(
        get_settings_text(settings),
        reply_markup=get_settings_keyboard(settings),
        parse_mode="HTML",
    )


@router.message(Command("settings"))
@router.message(F.text.contains("Настройки"))
async def settings_handler(message: Message):
    await show_settings(message)


# ---------------------------------------------------------------------------
# Частота напоминаний
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "settings:frequency")
async def frequency_settings_handler(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    if settings is None:
        await callback.answer("Не удалось загрузить настройки.", show_alert=True)
        return

    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            "⏱ <b>Частота напоминаний</b>\\n\\n"
            "Как часто отправлять тебе напоминания?",
            reply_markup=get_frequency_keyboard(settings.reminder_interval_hours),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("settings:interval:"))
async def set_frequency_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    interval_hours = int(callback.data.rsplit(":", maxsplit=1)[-1])

    if interval_hours not in REMINDER_INTERVALS:
        await callback.answer("Недопустимая частота напоминаний.", show_alert=True)
        return

    await set_reminder_interval_hours(telegram_id, interval_hours)
    settings = await get_user_settings(telegram_id)

    if settings is None:
        await callback.answer("Не удалось загрузить настройки.", show_alert=True)
        return

    await callback.answer("Частота напоминаний обновлена.")
    if callback.message:
        await callback.message.edit_text(
            get_settings_text(settings),
            reply_markup=get_settings_keyboard(settings),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------------
# Возврат к основным настройкам
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "settings:back")
async def settings_back_handler(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    if settings is None:
        await callback.answer("Не удалось загрузить настройки.", show_alert=True)
        return

    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            get_settings_text(settings),
            reply_markup=get_settings_keyboard(settings),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "settings:main")
async def settings_main_handler(callback: CallbackQuery):
    await callback.answer()

    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            logger.debug(
                "Не удалось убрать клавиатуру настроек у сообщения %s",
                callback.message.message_id,
            )

        await callback.message.answer(
            "🏠 <b>Главное меню</b>\n\nВыбери действие:",
            reply_markup=main_keyboard,
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------------
# Режим выбора следующего урока
# ---------------------------------------------------------------------------

@router.callback_query(
    F.data.in_({
        "settings:mode:course_order",
        "settings:mode:last_completed",
    })
)
async def lesson_mode_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    mode = callback.data.rsplit(":", maxsplit=1)[-1]

    try:
        await update_lesson_mode(telegram_id, mode)
    except (aiohttp.ClientError, TimeoutError):
        logger.exception("Не удалось обновить режим уроков пользователя %s", telegram_id)
        await callback.answer(
            "Не удалось связаться с учебной платформой.",
            show_alert=True,
        )
        return

    mode_name = "последовательный" if mode == "course_order" else "адаптивный"
    await callback.answer("Режим обновлён.")

    if callback.message:
        await callback.message.answer(
            f"Выбран <b>{mode_name} режим</b>.",
            parse_mode="HTML",
        )

    logger.info("Режим уроков пользователя %s изменён на %s", telegram_id, mode)


# ---------------------------------------------------------------------------
# Пауза и возобновление напоминаний
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "settings:toggle_reminders")
async def toggle_reminders_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    settings = await get_user_settings(telegram_id)

    if settings is None:
        await callback.answer("Не удалось загрузить настройки.", show_alert=True)
        return

    new_value = not settings.reminders_enabled
    await set_reminders_enabled(telegram_id, new_value)

    updated_settings = await get_user_settings(telegram_id)
    if updated_settings is None:
        await callback.answer(
            "Настройки обновлены, но не удалось их загрузить.",
            show_alert=True,
        )
        return

    status = "возобновлены" if new_value else "приостановлены"
    await callback.answer(f"Напоминания {status}.")

    if callback.message:
        await callback.message.edit_text(
            get_settings_text(updated_settings),
            reply_markup=get_settings_keyboard(updated_settings),
            parse_mode="HTML",
        )

    logger.info("Пользователь %s изменил состояние напоминаний: %s", telegram_id, status)


# ---------------------------------------------------------------------------
# Расписание напоминаний
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "settings:schedule")
async def schedule_settings_handler(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    if settings is None:
        await callback.answer("Не удалось загрузить расписание.", show_alert=True)
        return

    if callback.message:
        await callback.message.edit_text(
            get_schedule_text(),
            reply_markup=get_schedule_keyboard(settings.reminder_schedule),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("settings:schedule:"))
async def set_schedule_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    schedule_name = callback.data.rsplit(":", maxsplit=1)[-1]

    if schedule_name not in REMINDER_SCHEDULES:
        await callback.answer("Неизвестное расписание.", show_alert=True)
        return

    await set_reminder_schedule(telegram_id, schedule_name)
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
            parse_mode="HTML",
        )

    logger.info("Пользователь %s установил расписание: %s", telegram_id, schedule_name)
