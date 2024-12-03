from aiogram import Router
from aiogram.types import Message
from filters import ContainsForbiddenWord
from collections import defaultdict

# Создаём объект маршрутизатора
router = Router()

user_messages = defaultdict(list)
MESSAGE_LIMIT = 5  # Сообщений
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

