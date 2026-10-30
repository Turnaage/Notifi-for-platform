
import inspect

import main


def test_main_exposes_async_entry_point():
    assert hasattr(main, "main")
    assert callable(main.main)
    assert inspect.iscoroutinefunction(main.main)


def test_main_imports_required_routers():
    assert hasattr(main, "start_router")
    assert hasattr(main, "next_lesson_router")
    assert hasattr(main, "settings_router")


def test_main_imports_database_initialization():
    assert hasattr(main, "init_db")
    assert callable(main.init_db)


def test_main_imports_scheduler():
    assert hasattr(main, "scheduler")


def test_main_registers_all_required_routers():
    # Проверяем публичную конфигурацию Dispatcher.
    dp = getattr(main, "dp", None)
    assert dp is not None

    registered_routers = dp.sub_routers

    assert main.start_router in registered_routers
    assert main.next_lesson_router in registered_routers
    assert main.settings_router in registered_routers
