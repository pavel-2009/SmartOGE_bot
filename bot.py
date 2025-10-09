import logging
from aiogram.types import Update


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d in %(funcName)s(): %(message)s"
)

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from aiogram.types import BotCommand

from dotenv import load_dotenv
from os import getenv

from bot_handlers.start import start_router
from bot_handlers.quiz import quiz_router
from bot_handlers.stats import stats_router
from bot_handlers.raiting import raiting_router
from bot_handlers.admin.start import admin_router
from bot_handlers.admin.stats import admin_stats_router
from bot_handlers.admin.settings import admin_settings_router
import database.db as db


load_dotenv()


async def on_error(update: Update, exception: Exception):
    logger = logging.getLogger("bot")
    logger.exception("Unhandled exception: %s", exception)
    # Попытка ответить пользователю информативно
    try:
        if hasattr(update, "message") and update.message:
            await update.message.reply("Произошла ошибка. Попробуйте ещё раз позже.")
        elif hasattr(update, "callback_query") and update.callback_query:
            await update.callback_query.message.reply("Произошла ошибка. Попробуйте ещё раз позже.")
    except Exception:
        logger.exception("Failed to send error message to user.")
    return True


async def main() -> None:
    """Main function to start the bot."""
    token = getenv('BOT_TOKEN')
    if not token:
        raise RuntimeError("BOT_TOKEN не установлен. Положите токен в .env или в переменные окружения.")
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(admin_stats_router)
    dp.include_router(admin_settings_router)
    dp.include_router(quiz_router)
    dp.include_router(start_router)
    dp.include_router(stats_router)
    dp.include_router(raiting_router)

    # dp.errors.register(on_error)

    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="quiz", description="Начать викторину"),
        BotCommand(command="stats", description="Моя статистика"),
        BotCommand(command="help", description="Помощь"),
    ]

    await bot.set_my_commands(commands)

    db.create_db()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
