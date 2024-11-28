import os

from aiogram import Router, Bot
from aiogram.types import Message, ChatMemberAdministrator, ChatPermissions
from aiogram.filters import Command, CommandObject
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
    
    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.reply("Нельзя банить самого себя 🤪")
        return
    
    user_id = message.reply_to_message.from_user.id  
    admins = os.getenv('ADMIN_IDS')
    admins_list = [int(number.strip()) for number in admins.split(',')]
    if user_id in admins_list:
        await message.reply("Админов банишь? Ай-ай-ай 😈")
        return
    
    
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
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    # Проверяем, отвечает ли пользователь на сообщение
    if not message.reply_to_message:
        await message.reply("Команда должна быть ответом на сообщение пользователя, которого нужно разбанить.")
        return

    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.reply("Нельзя разбанить самого себя 🤪")
        return
    
    user_id = message.reply_to_message.from_user.id  
    admins = os.getenv('ADMIN_IDS')
    admins_list = [int(number.strip()) for number in admins.split(',')]
    if user_id in admins_list:
        await message.reply("Админов разбанить можешь, а забанить нет)")
        return
    

    try:
        # Снимаем бан с пользователя
        await message.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} успешно разбанен!")
    except TelegramBadRequest as e:
        # Обрабатываем ошибку, если не удалось разбанить пользователя
        await message.reply(f"Не удалось разбанить пользователя: {e}")

@router.message(Command("kick"))
async def kick_user(message: Message):
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    # Проверяем, отвечает ли команда на сообщение
    if not message.reply_to_message:
        await message.reply("Команда должна быть ответом на сообщение пользователя, которого нужно исключить.")
        return

    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.reply("Нельзя кикать самого себя 🤪")
        return
    
    user_id = message.reply_to_message.from_user.id  
    admins = os.getenv('ADMIN_IDS')
    admins_list = [int(number.strip()) for number in admins.split(',')]
    if user_id in admins_list:
        await message.reply("Админов кикаешь? Ай-ай-ай 😈")
        return
    

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
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    # Проверяем, является ли команда ответом на сообщение
    if not message.reply_to_message:
        await message.reply("Команда должна быть ответом на сообщение пользователя, которому вы хотите выдать предупреждение.")
        return

    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.reply("Нельзя предупреждать самого себя 🤪")
        return
    
    user_id = message.reply_to_message.from_user.id  
    admins = os.getenv('ADMIN_IDS')
    admins_list = [int(number.strip()) for number in admins.split(',')]
    if user_id in admins_list:
        await message.reply("Ой ой, а это уже не шутки.")
        return

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
    
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    # Проверяем, является ли команда ответом на сообщение
    if not message.reply_to_message:
        await message.reply("Команда должна быть ответом на сообщение пользователя, у которого нужно снять предупреждение.")
        return

    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.reply("Нельзя предупреждать самого себя 🤪")
        return
    
    user_id = message.reply_to_message.from_user.id  
    admins = os.getenv('ADMIN_IDS')
    admins_list = [int(number.strip()) for number in admins.split(',')]
    if user_id in admins_list:
        await message.reply("Ой ой, а это уже не шутки.")
        return

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

    warn_list = []
    for user_id, warn_count in warnings[chat_id].items():
        try:
            # Получаем информацию о пользователе
            member = await message.chat.get_member(user_id)
            user = member.user
            # Получаем юзернейм или полное имя
            if user.username:
                user_name = f"@{user.username}"
            else:
                user_name = f"{user.full_name}"
        except Exception:
            user_name = "Неизвестный пользователь"
        # Формируем строку с информацией о предупреждениях
        warn_list.append(f"{user_name} (ID: {user_id}): {warn_count} предупреждение(ий)")

    warn_list_str = "\n".join(warn_list)
    await message.reply(f"Список предупреждений:\n{warn_list_str}")
    
@router.message(Command("mute"))
async def mute_user(message: Message):
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    if not message.reply_to_message:
        await message.reply("Пожалуйста, используйте эту команду в ответ на сообщение пользователя.")
        return

    user_id = message.reply_to_message.from_user.id
    duration = 60  # Время мута в минутах

    until_date = datetime.now() + timedelta(minutes=duration)
    await message.chat.restrict(
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until_date
    )
    await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} замучен на {duration} минут.")
    
@router.message(Command("unmute"))
async def unmute_user(message: Message):
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    if not message.reply_to_message:
        await message.reply("Пожалуйста, используйте эту команду в ответ на сообщение пользователя.")
        return

    user_id = message.reply_to_message.from_user.id
    await message.chat.restrict(
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=True)
    )
    await message.reply(f"С пользователя {message.reply_to_message.from_user.full_name} снят мут.")
    
@router.message(Command("poll"))
async def create_poll(message: Message, command: CommandObject):
    
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        await message.reply("У вас недостаточно прав!")
        return
    
    args = command.args
    if not args:
        await message.reply("Пожалуйста, укажите вопрос и варианты ответа через '|'. Пример: /poll Ваш вопрос | Вариант 1 | Вариант 2")
        return

    parts = args.split('|')
    if len(parts) < 2:
        await message.reply("Пожалуйста, укажите хотя бы один вариант ответа.")
        return

    question = parts[0].strip()
    options = [option.strip() for option in parts[1:]]

    await message.answer_poll(
        question=question,
        options=options,
        is_anonymous=True
    )