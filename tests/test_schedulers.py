
import scheduler as scheduler_module

from unittest.mock import AsyncMock

from apscheduler.schedulers.asyncio import AsyncIOScheduler




def test_scheduler_is_async_scheduler():
    assert isinstance(
        scheduler_module.scheduler,
        AsyncIOScheduler,
    )

