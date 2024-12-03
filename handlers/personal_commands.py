import os
from aiogram import Router, Bot, F
from aiogram.types import Message, ChatMemberUpdated
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Создаём объект маршрутизатора
router = Router()

@router.message()
async def handle_messages(message: Message):
    """
    Обрабатывает сообщения, отправленные боту в личных сообщениях.

    Если бот получает сообщение в приватном чате, он отвечает стандартным сообщением.

    Args:
        message (Message): Сообщение, отправленное в чат.
    """
    if message.chat.type == 'private':  # Проверяем, что сообщение отправлено в приватный чат
        await message.reply("Я бот для чата Вольта!")  # Ответное сообщение


@router.chat_member()
async def welcome_new_member(event: ChatMemberUpdated):
    """
    Приветствует новых участников чата.

    Если новый участник вступает в чат, бот отправляет приветственное сообщение
    с предложением ознакомиться с правилами чата.

    Args:
        event (ChatMemberUpdated): Событие изменения статуса участника чата.
    """

    new_member = event.new_chat_member  # Информация о новом участнике
    if new_member.status == "member":  # Проверяем, что участник только что вступил в чат
        user = new_member.user  # Получаем информацию о пользователе
        chat_id = event.chat.id
        TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')
        TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)
        if chat_id == TELEGRAM_CHAT_ID:
            await event.bot.send_message(
                chat_id,  # ID чата, куда отправить сообщение
                f"Добро пожаловать, {user.full_name}! Пожалуйста, ознакомьтесь с правилами чата, использовав команду /rules."
            )
        
