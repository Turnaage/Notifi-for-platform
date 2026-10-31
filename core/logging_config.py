
import logging
from logging.handlers import RotatingFileHandler
from core.config import MAX_LOG_SIZE, BACKUP_COUNT, BASE_DIR, LOG_DIR, LOG_FORMAT, DATE_FORMAT


def create_file_handler(
    filename: str,
    level: int = logging.INFO,
) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )

    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            LOG_FORMAT,
            datefmt=DATE_FORMAT,
        )
    )

    return handler


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if getattr(root_logger, "_notify_logging_configured", False):
        return

    root_logger.addHandler(
        create_file_handler("app.log")
    )

    root_logger.addHandler(
        create_file_handler(
            "errors.log",
            logging.ERROR,
        )
    )

    components = {
        "services.api": "api.log",
        "database": "database.log",
        "handlers": "bot.log",
        "services.reminders": "reminders.log",
        "scheduler": "scheduler.log",
    }

    for logger_name, filename in components.items():
        component_logger = logging.getLogger(logger_name)

        component_logger.addHandler(
            create_file_handler(filename)
        )

        component_logger.setLevel(logging.INFO)
        component_logger.propagate = True

    root_logger._notify_logging_configured = True

    logging.getLogger(__name__).info(
        "Система логирования запущена"
    )
