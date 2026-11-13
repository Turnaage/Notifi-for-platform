from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.config import REMINDER_SCHEDULES
from schemas.user_settings import UserSettings



def is_reminder_time(settings: UserSettings) -> bool:
    """
    Проверяет, разрешено ли отправлять напоминание
    в текущий момент по расписанию пользователя.
    """
    schedule = REMINDER_SCHEDULES[settings.reminder_schedule]

    try:
        local_now = datetime.now(ZoneInfo(settings.timezone))
    except (ZoneInfoNotFoundError, ValueError):
        local_now = datetime.now(ZoneInfo("Europe/Moscow"))

    if local_now.weekday() < 5:
        start_time, end_time = schedule["weekday"]
    else:
        start_time, end_time = schedule["weekend"]

    current_time = local_now.strftime("%H:%M")

    return start_time <= current_time < end_time