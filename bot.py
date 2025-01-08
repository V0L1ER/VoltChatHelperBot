import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import admin_commands, moderation, personal_commands, user_commands
from database.database import init_db
from utils.logger import BotLogger
from config import get_settings
from middlewares.spam_filter import spam_filter

# Инициализируем логгер
logger = BotLogger.setup()

# Получаем настройки
settings = get_settings()

# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def main():
    # Подключение маршрутов для различных команд
    dp.include_router(user_commands.router)
    dp.include_router(admin_commands.router)
    dp.include_router(moderation.router)
    dp.include_router(personal_commands.router)  # Перемещаем в конец
    
    dp.message.outer_middleware(spam_filter)

    # Инициализация базы данных
    await init_db()

    try:
        logger.info("Bot started successfully")
        print("Bot started successfully")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during bot execution: {e}", exc_info=True)
        print(f"Error during bot execution: {e}")
    finally:
        logger.info("Bot stopped")
        print("Bot stopped")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
