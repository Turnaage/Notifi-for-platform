
import inspect

from services import reminders


def test_reminder_service_exposes_async_entry_point():
    assert hasattr(reminders, "check_reminders")
    assert callable(reminders.check_reminders)
    assert inspect.iscoroutinefunction(reminders.check_reminders)


def test_reminder_service_exposes_no_required_real_connections():
    # Проверяем только наличие точки входа: импорт модуля не должен
    # сам запускать polling, scheduler или отправку сообщений.
    assert callable(reminders.check_reminders)
