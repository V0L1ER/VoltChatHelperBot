from aiogram import Router
from aiogram.types import Message, ChatPermissions
from filters import ContainsForbiddenWord
from collections import defaultdict
import time

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
    
    
@router.message()
async def anti_spam_handler(message: Message):
    
    if message.is_command():
        return  # Позволяет другим обработчикам обрабатывать команды
    
    user_id = message.from_user.id
    current_time = time.time()
    
    # Обновление списка временных меток сообщений пользователя
    user_messages[user_id] = [timestamp for timestamp in user_messages[user_id] if current_time - timestamp < TIME_WINDOW]
    user_messages[user_id].append(current_time)
    
    if len(user_messages[user_id]) > MESSAGE_LIMIT:
        # Проверяем, есть ли уже активные санкции
        member = await message.chat.get_member(user_id)
        if member.status in ['member', 'restricted']:
            # Отправляем предупреждение
            await message.reply(f"{message.from_user.first_name}, пожалуйста, не спамьте. У вас {len(user_messages[user_id])} сообщений за {TIME_WINDOW} секунд.")
            
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
            user_messages[user_id] = []
