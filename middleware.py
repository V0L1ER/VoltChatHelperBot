from aiogram import BaseMiddleware, types
from aiogram.types import ChatPermissions
import time
from collections import defaultdict

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, time_window: int, message_limit: int):
        super(AntiSpamMiddleware, self).__init__()
        self.time_window = time_window
        self.message_limit = message_limit
        self.user_messages = defaultdict(list)

    async def on_pre_process_message(self, message: types.Message, data: dict):
        # Игнорировать команды
        if message.is_command():
            return
        
        user_id = message.from_user.id
        current_time = time.time()
        
        # Обновление списка временных меток сообщений пользователя
        self.user_messages[user_id] = [
            timestamp for timestamp in self.user_messages[user_id]
            if current_time - timestamp < self.time_window
        ]
        self.user_messages[user_id].append(current_time)
        
        if len(self.user_messages[user_id]) > self.message_limit:
            # Проверяем, есть ли уже активные санкции
            member = await message.chat.get_member(user_id)
            if member.status in ['member', 'restricted']:
                # Отправляем предупреждение
                await message.reply(
                    f"{message.from_user.first_name}, пожалуйста, не спамьте. У вас {len(self.user_messages[user_id])} сообщений за {self.time_window} секунд."
                )
                
                # Применяем временный мут
                await message.chat.restrict(
                    user_id,
                    permissions=ChatPermissions(
                        send_messages=False
                    ),
                    until_date=time.time() + 300  # Мут на 5 минут
                )
                await message.reply(f"{message.from_user.first_name} был(а) временно замучен(а) за спам.")
                
                # Очистка списка сообщений после применения санкций
                self.user_messages[user_id] = []
                