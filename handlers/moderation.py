from aiogram import Router
from aiogram.types import Message
from filters import ContainsForbiddenWord

# Создаём объект маршрутизатора
router = Router()

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
