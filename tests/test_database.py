
import inspect

from database import db
from database import models


def test_database_exposes_required_operations():
    for name in (
        "ensure_user",
        "get_user",
        "set_reminders_enabled",
    ):
        operation = getattr(db, name)
        assert callable(operation)
        assert inspect.iscoroutinefunction(operation)


def test_models_contain_reminder_fields():
    user_columns = models.User.__table__.columns
    settings_columns = models.UserSettings.__table__.columns
    notification_columns = models.Notification.__table__.columns

    assert {"id", "telegram_id"}.issubset(user_columns.keys())

    assert {
        "id",
        "reminders_enabled",
        "reminder_interval_hours",
        "reminder_schedule",
        "timezone",
    }.issubset(settings_columns.keys())

    assert {
        "id",
        "user_id",
        "created_at",
        "updated_at",
    }.issubset(notification_columns.keys())


def test_telegram_id_is_unique_in_user_table():
    column = models.User.__table__.columns["telegram_id"]

    assert column.primary_key or column.unique
