import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import admin_commands, moderation, personal_commands, user_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta
from googleapiclient.discovery import build

# Загружаем переменные окружения из файла .env
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))  # Токен бота из переменных окружения
dp = Dispatcher(storage=MemoryStorage())  # Используем память для хранения состояний

# Константы
TELEGRAM_CHAT_ID = os.getenv('CHANNEL_ID')  # ID чата/канала для отправки уведомлений
TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')  # API-ключ для YouTube Data API
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')  # ID YouTube-канала для отслеживания

# Инициализация клиента YouTube API
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Переменная для хранения ID последнего видео
last_video_id = None


def get_latest_video_info():
    """
    Получает информацию о последнем видео на YouTube-канале.

    Запрашивает данные с помощью YouTube Data API и возвращает информацию о последнем видео:
    - ID видео
    - Заголовок видео
    - Описание видео

    Returns:
        tuple: (video_id, title, description) — ID видео, заголовок и описание.
        Если видео не найдено, возвращает (None, None, None).
    """
    request = youtube.search().list(
        part='snippet',  # Запрашиваем только часть 'snippet' для получения информации
        channelId=YOUTUBE_CHANNEL_ID,  # ID канала
        order='date',  # Сортируем по дате публикации
        maxResults=1,  # Запрашиваем только одно последнее видео
        type='video'  # Указываем, что ищем только видео
    )
    response = request.execute()  # Выполняем запрос к YouTube API
    items = response.get('items', [])  # Получаем список результатов
    if items:
        video_id = items[0]['id']['videoId']  # ID видео
        title = items[0]['snippet']['title']  # Заголовок видео
        description = items[0]['snippet']['description']  # Описание видео
        return video_id, title, description
    return None, None, None  # Возвращаем None, если видео не найдено

async def check_new_video():
    """
    Периодически проверяет наличие нового видео на YouTube-канале.

    Если обнаруживается новое видео, отправляет сообщение в указанный Telegram-чат с информацией о видео.
    Использует глобальную переменную `last_video_id` для отслеживания последнего видео.
    """
    global last_video_id  # Используем глобальную переменную для хранения последнего ID видео
    while True:
        try:
            video_id, title, description = get_latest_video_info()  # Получаем данные о последнем видео
            if video_id and video_id != last_video_id:
                # Формируем URL видео и текст сообщения
                video_url = f'https://www.youtube.com/watch?v={video_id}'
                message = f'Новое видео на канале!\n\n{title}\n{video_url}'
                #  await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)  # Отправляем сообщение в Telegram
                last_video_id = video_id  # Обновляем ID последнего видео
            await asyncio.sleep(3600)  # Пауза между проверками (1 час)
        except Exception as e:
            print(f'Ошибка при проверке нового видео: {e}')
            await asyncio.sleep(300)  # Пауза перед следующей попыткой при ошибке
 
@dp.startup()
async def on_startup():
    """
    Выполняется при запуске бота.

    Создаёт задачу для проверки новых видео на YouTube-канале.
    """
    asyncio.create_task(check_new_video())

async def main():
    """
    Основная функция запуска бота.

    - Подключает маршруты (handlers) из модулей.
    - Запускает процесс обработки обновлений (polling).
    """
    # Подключение маршрутов для различных команд
    dp.include_router(moderation.router)  # Маршруты модерации
    dp.include_router(admin_commands.router)  # Административные команды
    dp.include_router(user_commands.router)  # Команды для пользователей
    dp.include_router(personal_commands.router)  # Личные команды

    try:
        print("Bot Start")  # Сообщение о запуске бота
        await dp.start_polling(bot)  # Запускаем polling
    finally:
        await bot.session.close()  # Закрываем сессию бота при завершении работы

if __name__ == "__main__":
    """
    Точка входа в приложение.

    Запускает основную функцию `main()` и обрабатывает прерывания (Ctrl+C).
    """
    try:
        asyncio.run(main())  # Запускаем основную функцию
    except KeyboardInterrupt:
        print("Exit")  # Выводим сообщение при завершении работы
