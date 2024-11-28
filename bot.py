import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import admin_commands, moderation, personal_commands, user_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta
from googleapiclient.discovery import build

load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage())

TELEGRAM_CHAT_ID = os.getenv('CHANNEL_ID') 
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

last_video_id = None

def get_latest_video_info():
    request = youtube.search().list(
        part='snippet',
        channelId=YOUTUBE_CHANNEL_ID,
        order='date',
        maxResults=1,
        type='video'
    )
    response = request.execute()
    items = response.get('items', [])
    if items:
        video_id = items[0]['id']['videoId']
        title = items[0]['snippet']['title']
        description = items[0]['snippet']['description']
        return video_id, title, description
    return None, None, None

async def check_new_video():
    global last_video_id
    while True:
        try:
            video_id, title, description = get_latest_video_info()
            if video_id and video_id != last_video_id:
                video_url = f'https://www.youtube.com/watch?v={video_id}'
                message = f'Новое видео на канале!\n\n{title}\n{video_url}'
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                last_video_id = video_id
            else:
                print('Нет новых видео.')
            await asyncio.sleep(300)  # Проверяем каждые 5 минут
        except Exception as e:
            print(f'Ошибка при проверке нового видео: {e}')
            await asyncio.sleep(300)

@dp.startup()
async def on_startup():
    asyncio.create_task(check_new_video())

async def main():
    # Инициализация бота и диспетчера
    
    
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
        
    