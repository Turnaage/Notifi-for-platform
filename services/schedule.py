from datetime import datetime
from zoneinfo import ZoneInfo


REMINDER_SCHEDULES = {
    "after_work": {
        "name": "После работы",
        "weekday": ("18:00", "22:00"),
        "weekend": ("10:00", "20:00"),
    },
    "morning": {
        "name": "Утреннее",
        "weekday": ("07:00", "09:00"),
        "weekend": ("09:00", "12:00"),
    },
    "evening": {
        "name": "Вечернее",
        "weekday": ("18:00", "22:00"),
        "weekend": ("18:00", "22:00"),
    },
}


def is_reminder_time(
    schedule_name: str,
    timezone: str,
) -> bool:
    """
    Проверяет, разрешено ли отправлять напоминание
    в текущий момент по расписанию пользователя.
    """

    schedule = REMINDER_SCHEDULES.get(schedule_name)

    if schedule is None:
        schedule = REMINDER_SCHEDULES["after_work"]

    try:
        local_now = datetime.now(ZoneInfo(timezone))
    except Exception:
        local_now = datetime.now(ZoneInfo("Europe/Moscow"))

    # Понедельник — пятница
    if local_now.weekday() < 5:
        start_time, end_time = schedule["weekday"]
    else:
        start_time, end_time = schedule["weekend"]

    current_time = local_now.strftime("%H:%M")

    return start_time <= current_time < end_time