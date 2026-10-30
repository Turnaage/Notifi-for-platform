import asyncio

from database.db import init_db, close_db, ensure_user, get_user


async def main():
    try:
        await init_db()

        test_telegram_id = 123456789
        await ensure_user(test_telegram_id)

        user = await get_user(test_telegram_id)

        if user:
            print("PostgreSQL: подключение работает")
            print(f"Telegram ID: {user.telegram_id}")
            print(f"Напоминания включены: {user.reminders_enabled}")
        else:
            print("Пользователь не найден")

    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())