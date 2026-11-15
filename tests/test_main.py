
import inspect
import main


def test_main_exposes_async_entry_point():
    assert hasattr(main, "main")
    assert callable(main.main)
    assert inspect.iscoroutinefunction(main.main)


def test_main_imports_required_routers():
    assert hasattr(main, "router")
    assert hasattr(main, "start")
    assert hasattr(main, "next_lesson")
    assert hasattr(main, "settings")
    assert hasattr(main, "survey")



def test_main_imports_scheduler():
    assert hasattr(main, "scheduler")


def test_main_registers_all_required_routers():
    # Проверяем публичную конфигурацию Dispatcher.
    dp = getattr(main, "dp", None)
    assert dp is not None

    registered_routers = dp.sub_routers

    assert main.router in registered_routers
