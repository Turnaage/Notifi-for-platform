from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reminders_enabled: bool = True

    reminder_interval_hours: Literal[24, 48, 72, 168] = 48

    reminder_schedule: Literal[
        "after_work",
        "morning",
        "evening",
    ] = "after_work"

    timezone: str = "Europe/Moscow"