import asyncio
import argparse

from core.bot import create_bot
from services.survey import (
    send_test_survey,
    send_monthly_surveys
)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="Отправить тестовое сообщение только себе"
    )

    args = parser.parse_args()

    bot = create_bot()

    try:
        if args.test:
            print("Запуск тестовой отправки...")
            await send_test_survey(bot)
            print("Тестовое сообщение успешно отправлено")

        else:
            print("Запуск ежемесячной рассылки...")
            await send_monthly_surveys(bot)
            print("Ежемесячная рассылка завершена")

    except Exception as e:
        print(f"Ошибка рассылки: {e}")
        raise

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
