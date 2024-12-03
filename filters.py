from aiogram.filters import BaseFilter
from aiogram.types import Message

class ContainsForbiddenWord(BaseFilter):
    """
    Кастомный фильтр для проверки наличия запрещённых слов в сообщении.

    Атрибуты:
        forbidden_words (list): Список запрещённых слов.
    """
    forbidden_words = ["хохол", "гитлер", "сталин"]  # Список запрещённых слов

    async def __call__(self, message: Message) -> bool:
        """
        Проверяет, содержит ли сообщение одно из запрещённых слов.

        Args:
            message (Message): Сообщение, отправленное в чате.

        Returns:
            bool: True, если сообщение содержит запрещённые слова; False иначе.
        """
        # Проверяем, что текст сообщения существует и ищем запрещённые слова
        if message.text:
            # Приводим текст к нижнему регистру и проверяем на наличие запрещённых слов
            return any(word in message.text.lower() for word in self.forbidden_words)
        return False
