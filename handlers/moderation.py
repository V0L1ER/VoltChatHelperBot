from aiogram import Router
from aiogram.types import Message
from filters import ContainsForbiddenWord
from collections import defaultdict
import time

# Создаём объект маршрутизатора
router = Router()

user_message_times = defaultdict(list)
SPAM_LIMIT = 5  # Сообщений
TIME_WINDOW = 60  # Секунд

@router.message(ContainsForbiddenWord())
async def handle_forbidden_words(message: Message):
    """
    Обработчик сообщений с запрещёнными словами.

    Если сообщение содержит запрещённые слова:
    - Удаляет сообщение.
    - Отправляет уведомление о том, что сообщение было удалено.

    Args:
        message (Message): Сообщение, содержащее запрещённые слова.
    """
    await message.delete()  # Удаляем сообщение с запрещённым словом
    await message.answer(f"Сообщение с запрещёнными словами было удалено.")  # Уведомляем об удалении
    
    
router.message()
async def anti_spam_handler(message: Message):
    user_id = message.from_user.id
    current_time = time.time()

    # Очистка старых временных меток
    user_message_times[user_id] = [
        timestamp for timestamp in user_message_times[user_id]
        if current_time - timestamp < TIME_WINDOW
    ]

    # Добавление текущего сообщения
    user_message_times[user_id].append(current_time)

    # Проверка лимита
    if len(user_message_times[user_id]) > SPAM_LIMIT:
        try:
            await message.delete()
            await message.reply(f"{message.from_user.first_name}, пожалуйста, не спамьте!")
        except Exception as e:
            print(f"Ошибка при удалении сообщения или отправке предупреждения: {e}")
