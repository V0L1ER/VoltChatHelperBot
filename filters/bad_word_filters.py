from aiogram.filters import BaseFilter
from aiogram.types import Message
from config import get_settings

settings = get_settings()

class ContainsForbiddenWord(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text:
            return any(word in message.text.lower() for word in settings.FORBIDDEN_WORDS)
        return False
