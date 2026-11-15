import argparse
import asyncio

from core.bot import create_bot
from core.logging_config import setup_logging
from database.db import close_db
from services.survey import (
    send_test_survey,
    send_monthly_surveys,
)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="Отправить тестовое сообщение только себе",
    )

    args = parser.parse_args()

    setup_logging()

    bot = create_bot()

    try:
        if args.test:
            print("Запуск тестовой отправки...")
            await send_test_survey(bot)
            print("Тестовое сообщение успешно отправлено")
            return

        print("Запуск ежемесячной рассылки...")
        result = await send_monthly_surveys(bot)
        print(
            "Ежемесячная рассылка завершена. "
            f"Всего: {result['total']}, "
            f"отправлено: {result['sent']}, "
            f"ошибок: {result['failed']}"
        )

        if result["total"] > 0 and result["sent"] == 0:
            raise RuntimeError(
                "Не удалось отправить ни одного опроса"
            )

    except Exception as error:
        print(f"Ошибка рассылки: {error}")
        raise

    finally:
        try:
            await bot.session.close()
        finally:
            await close_db()


if __name__ == "__main__":
    asyncio.run(main())
