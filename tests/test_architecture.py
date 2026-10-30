
import importlib
import inspect

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "core.config",
        "core.bot",
        "database.db",
        "database.models",
        "handlers.start",
        "handlers.next_lesson",
        "handlers.settings",
        "services.api",
        "services.reminders",
        "scheduler",
    ],
)
def test_required_module_can_be_imported(module_name):
    importlib.import_module(module_name)


@pytest.mark.parametrize(
    ("module_name", "function_name"),
    [
        ("database.db", "ensure_user"),
        ("database.db", "get_user"),
        ("database.db", "set_reminders_enabled"),
        ("services.api", "get_next_lesson"),
        ("services.api", "get_progress"),
        ("services.api", "update_lesson_mode"),
        ("services.reminders", "check_reminders"),
    ],
)
def test_required_public_function_exists(module_name, function_name):
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)

    assert callable(function)


@pytest.mark.parametrize(
    ("module_name", "function_name"),
    [
        ("database.db", "ensure_user"),
        ("database.db", "get_user"),
        ("database.db", "set_reminders_enabled"),
        ("services.api", "get_next_lesson"),
        ("services.api", "get_progress"),
        ("services.api", "update_lesson_mode"),
        ("services.reminders", "check_reminders"),
    ],
)
def test_required_operations_are_async(module_name, function_name):
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)

    assert inspect.iscoroutinefunction(function)
