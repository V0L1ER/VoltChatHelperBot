from aiogram import BaseMiddleware
from aiogram.types import Message, Update
from typing import Any, Awaitable, Callable, Dict
from collections import defaultdict
import time
from config import get_settings
import asyncio
from utils.logger import BotLogger

logger = BotLogger.get_logger()
settings = get_settings()

class SpamFilter(BaseMiddleware):
    def __init__(self):
        self.user_messages = defaultdict(list)
        super().__init__()  # Добавляем вызов конструктора родительского класса
        
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        
        if not isinstance(event, Message):
            return await handler(event, data)
            
        # Пропускаем сообщения от администраторов
        if event.sender_chat:
            if event.sender_chat.id in [int(settings.CHANNEL_ID), int(settings.CHAT_ID)]:
                return await handler(event, data)
                
        if str(event.from_user.id) in settings.ADMIN_IDS.split(','):
            return await handler(event, data)
            
        try:
            member = await event.chat.get_member(event.from_user.id)
            if member.status in ['administrator', 'creator']:
                return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка при проверке прав администратора: {e}")
            
        # Получаем текущее время
        current_time = time.time()
        user_id = event.from_user.id
        
        # Очищаем старые сообщения
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if current_time - msg_time < settings.SPAM_TIME_WINDOW
        ]
        
        # Добавляем новое сообщение
        self.user_messages[user_id].append(current_time)
        
        # Проверяем на спам
        if len(self.user_messages[user_id]) > settings.SPAM_MESSAGE_LIMIT:
            try:
                # Удаляем сообщение
                await event.delete()
                
                # Если это повторный спам в течение минуты
                recent_warns = [
                    t for t in self.user_messages.get(f"warn_{user_id}", [])
                    if current_time - t < 60  # 60 секунд = 1 минута
                ]
                
                if recent_warns:
                    # Мутим пользователя на 10 минут
                    until_date = current_time + 600  # 600 секунд = 10 минут
                    await event.chat.restrict(
                        user_id=user_id,
                        permissions={"can_send_messages": False},
                        until_date=until_date
                    )
                    await event.answer(
                        f"🚫 Пользователь получает мут на 10 минут за повторный спам!"
                    )
                else:
                    # Первое предупреждение
                    warn_msg = await event.answer(
                        "⚠️ Пожалуйста, не отправляйте сообщения слишком часто!"
                    )
                    # Сохраняем время предупреждения
                    self.user_messages.setdefault(f"warn_{user_id}", []).append(current_time)
                    
                    # Удаляем предупреждение через некоторое время
                    await asyncio.sleep(settings.SPAM_WARN_DELETION_DELAY)
                    await warn_msg.delete()
                
                return None
                
            except Exception as e:
                logger.error(f"Ошибка при обработке спама: {e}")
                return await handler(event, data)
                
        return await handler(event, data)

# Создаем экземпляр фильтра
spam_filter = SpamFilter()