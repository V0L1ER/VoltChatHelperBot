from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Any, Awaitable, Callable
from utils.logger import BotLogger

logger = BotLogger.get_logger()

class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка при обработке события: {e}", exc_info=True)
            # Отправляем уведомление администраторам в sharechat
            from config import get_settings
            settings = get_settings()
            try:
                await event.bot.send_message(
                    chat_id=settings.SHARECHAT_ID,
                    text=f"❗️ Произошла ошибка в боте:\n{str(e)}\n\nСобытие: {event}"
                )
            except Exception as notify_error:
                logger.error(f"Не удалось отправить уведомление об ошибке: {notify_error}")
            return None 