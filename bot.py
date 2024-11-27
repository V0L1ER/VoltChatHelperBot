import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import admin_commands, moderation, personal_commands, user_commands
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(moderation.router)
    dp.include_router(admin_commands.router)
    dp.include_router(user_commands.router)
    dp.include_router(personal_commands.router)

    try:
        print("Bot Start")
        await bot.set_my_commands([
        BotCommand(command="ban", description="Заблокировать пользователя"),
        ])

        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
        
    