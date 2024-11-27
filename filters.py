from aiogram.filters import BaseFilter
from aiogram.types import Message

class ContainsForbiddenWord(BaseFilter):
    forbidden_words = ["spam", "badword"]  # Список запрещённых слов

    async def __call__(self, message: Message) -> bool:
        # Проверяем, что текст присутствует и ищем запрещённые слова
        if message.text:
            return any(word in message.text.lower() for word in self.forbidden_words)
        return False
