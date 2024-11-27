import os

from aiogram import Router
from aiogram.types import Message, ChatMemberAdministrator
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

load_dotenv()

router = Router()

warnings = {}

@router.message(Command("ban"))
async def ban_user(message: Message):
    
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть использована как ответ на сообщение.")
        return
    
    user_id = message.reply_to_message.from_user.id
    
    # Проверяем права бота
    bot_member = await message.bot.get_chat_member(chat_id, message.bot.id)
    if not isinstance(bot_member, ChatMemberAdministrator) or not bot_member.can_restrict_members:
        await message.reply("У меня недостаточно прав для блокировки участников. Проверьте мои права администратора.")
        return

    try:
        # Выполняем бан
        await message.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await message.answer(f"Пользователь {message.reply_to_message.from_user.full_name} был заблокирован.")
    except Exception as e:
        await message.reply(f"Ошибка при попытке заблокировать пользователя: {e}")
        
@router.message(Command("unban"))
async def unban_user(message: Message):
    
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    # Проверяем, отвечает ли пользователь на сообщение
    if not message.reply_to_message:
        await message.reply("Команда должна быть ответом на сообщение пользователя, которого нужно разбанить.")
        return

    # Получаем ID пользователя, которого нужно разбанить
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        # Снимаем бан с пользователя
        await message.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} успешно разбанен!")
    except TelegramBadRequest as e:
        # Обрабатываем ошибку, если не удалось разбанить пользователя
        await message.reply(f"Не удалось разбанить пользователя: {e}")

@router.message(Command("kick"))
async def kick_user(message: Message):
    
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    # Проверяем, отвечает ли команда на сообщение
    if not message.reply_to_message:
        await message.reply("Команда должна быть ответом на сообщение пользователя, которого нужно исключить.")
        return

    # Получаем ID пользователя, которого нужно исключить
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        # Исключаем пользователя из чата
        await message.bot.ban_chat_member(chat_id=chat_id, user_id=user_id, until_date=0)
        await message.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} успешно исключён из чата!")
    except TelegramBadRequest as e:
        # Обрабатываем ошибки, если исключение невозможно
        await message.reply(f"Не удалось исключить пользователя: {e}")

@router.message(Command("warn"))
async def warn_user(message: Message):
    
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    # Проверяем, является ли команда ответом на сообщение
    if not message.reply_to_message:
        await message.reply("Команда должна быть ответом на сообщение пользователя, которому вы хотите выдать предупреждение.")
        return

    # Получаем ID пользователя и чата
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    # Увеличиваем количество предупреждений
    if chat_id not in warnings:
        warnings[chat_id] = {}

    if user_id not in warnings[chat_id]:
        warnings[chat_id][user_id] = 0

    warnings[chat_id][user_id] += 1
    current_warnings = warnings[chat_id][user_id]

    # Отправляем предупреждение пользователю
    await message.reply(
        f"Пользователю {message.reply_to_message.from_user.full_name} вынесено предупреждение. "
        f"Это {current_warnings}-е предупреждение."
    )

    # Проверяем, достиг ли пользователь лимита предупреждений
    max_warnings = 3  # Максимальное количество предупреждений
    if current_warnings >= max_warnings:
        await message.reply(
            f"Пользователь {message.reply_to_message.from_user.full_name} достиг максимального количества предупреждений и будет исключён."
        )
        # Исключаем пользователя из чата
        await message.bot.ban_chat_member(chat_id=chat_id, user_id=user_id, until_date=0)
        await message.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        # Сбрасываем предупреждения после исключения
        warnings[chat_id][user_id] = 0
        
@router.message(Command("remwarn"))
async def remove_warn(message: Message):
    # Проверяем, является ли команда ответом на сообщение
    if not message.reply_to_message:
        await message.reply("Команда должна быть ответом на сообщение пользователя, у которого нужно снять предупреждение.")
        return

    # Получаем ID пользователя и чата
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    # Проверяем, есть ли предупреждения у пользователя
    if chat_id not in warnings or user_id not in warnings[chat_id] or warnings[chat_id][user_id] == 0:
        await message.reply(f"У пользователя {message.reply_to_message.from_user.full_name} нет активных предупреждений.")
        return

    # Уменьшаем количество предупреждений
    warnings[chat_id][user_id] -= 1
    current_warnings = warnings[chat_id][user_id]

    await message.reply(
        f"Одно предупреждение пользователя {message.reply_to_message.from_user.full_name} было удалено. "
        f"Теперь у него {current_warnings} предупреждений."
    )
    
@router.message(Command("listwarns"))
async def list_warns(message: Message):
    chat_id = message.chat.id

    if chat_id not in warnings or not warnings[chat_id]:
        await message.reply("В этом чате нет пользователей с предупреждениями.")
        return

    warn_list = "\n".join(
        [f"{user_id}: {warn_count} предупреждений" for user_id, warn_count in warnings[chat_id].items()]
    )
    await message.reply(f"Список предупреждений:\n{warn_list}")