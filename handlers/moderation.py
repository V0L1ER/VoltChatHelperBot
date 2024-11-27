from aiogram import Router
from aiogram.types import Message
from filters import ContainsForbiddenWord

router = Router()

@router.message(ContainsForbiddenWord())
async def handle_forbidden_words(message: Message):
    await message.delete()  # Удаляем сообщение с запрещённым словом
    await message.answer(f"Сообщение с запрещёнными словами было удалено.")
