
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


def test_user_model_contains_reminder_fields():
    user_columns = models.User.__table__.columns

    required_columns = {
        "telegram_id",
        "reminders_enabled",
        "reminder_interval_hours",
        "last_reminder_sent_at",
        "created_at",
        "updated_at",
    }

    assert required_columns.issubset(set(user_columns.keys()))


def test_telegram_id_is_unique_in_user_table():
    column = models.User.__table__.columns["telegram_id"]

    assert column.primary_key or column.unique
