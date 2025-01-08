import os
from aiogram import Router, Bot, F
from aiogram.types import Message, ChatMemberAdministrator, ChatPermissions, ChatMemberOwner, ChatMemberBanned
from aiogram.filters import Command, CommandObject, BaseFilter
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from database.database import AsyncSessionLocal
from database.models import Warning, UserStats
from datetime import datetime
from config import get_settings
from utils.logger import BotLogger
from typing import Tuple, Optional
from sqlalchemy import select
from sqlalchemy import func
from functools import wraps
from utils.command_logging import log_command

# Загружаем переменные окружения из файла .env
load_dotenv()

# Создаём объект маршрутизатора для регистрации обработчиков
router = Router()

logger = BotLogger.get_logger()
settings = get_settings()

def allowed_chat_only():
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if message.chat.id != settings.CHAT_ID:
                logger.warning(
                    f"Попытка использования команды в неразрешенном чате: {message.chat.id}"
                )
                return
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # Проверяем список админов из конфига
        if str(message.from_user.id) in settings.ADMIN_IDS.split(','):
            return True
            
        # Проверяем сообщение от имени канала/чата
        if message.sender_chat:
            try:
                # Получаем информацию о владельце канала/чата
                chat_info = await message.bot.get_chat(message.sender_chat.id)
                if chat_info.type in ['channel', 'supergroup']:
                    # Проверяем, является ли отправитель владельцем канала/чата
                    admins = await message.bot.get_chat_administrators(message.chat.id)
                    for admin in admins:
                        if isinstance(admin, ChatMemberOwner):
                            return True
            except Exception as e:
                logger.error(f"Error checking channel/chat admin rights: {e}")
                return False
            
        # Проверяем обычные права в чате
        try:
            chat_member = await message.chat.get_member(message.from_user.id)
            return isinstance(chat_member, (ChatMemberOwner, ChatMemberAdministrator))
        except Exception as e:
            logger.error(f"Error checking admin rights: {e}")
            return False

# Применяем фильтр ко всем хендлерам в роутере
router.message.filter(IsAdmin())

async def check_admin_rights(message: Message) -> Tuple[bool, Optional[str]]:
    """Проверка прав администратора"""
    if message.sender_chat:
        if message.sender_chat.id in [int(settings.CHANNEL_ID), int(settings.CHAT_ID)]:
            return True, None
        return False, "У вас недостаточно прав!"
    
    try:
        admin_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if isinstance(admin_member, (ChatMemberOwner, ChatMemberAdministrator)):
            return True, None
        return False, "У вас недостаточно прав!"
    except Exception as e:
        logger.error(f"Error checking admin rights: {e}")
        return False, "Ошибка при проверке прав администратора."

async def check_bot_rights(message: Message) -> Tuple[bool, Optional[str]]:
    """Проверка прав бота"""
    try:
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if isinstance(bot_member, ChatMemberAdministrator) and bot_member.can_restrict_members:
            return True, None
        return False, "У меня недостаточно прав для управления участниками."
    except Exception as e:
        logger.error(f"Error checking bot rights: {e}")
        return False, "Ошибка при проверке прав бота."

@router.message(Command("ban"))
@allowed_chat_only()
async def ban_user(message: Message):
    await log_command(message)
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть использована как ответ на сообщение.")
        return

    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    # Проверка прав бота
    bot_has_rights, error_msg = await check_bot_rights(message)
    if not bot_has_rights:
        await message.reply(error_msg)
        return

    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id

    try:
        # Проверяем особые случаи
        if str(user_id) in settings.ADMIN_IDS.split(','):
            await message.reply("Админов банишь? Ай-ай-ай 😈")
            return

        target_member = await message.bot.get_chat_member(chat_id, user_id)
        if isinstance(target_member, (ChatMemberOwner, ChatMemberAdministrator)):
            await message.reply("Невозможно забанить администратора.")
            return

        # Выполняем бан
        await message.bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            revoke_messages=True
        )

        await message.reply(
            f"Пользователь {message.reply_to_message.from_user.full_name} "
            f"(id: {user_id}) был заблокирован."
        )
        logger.info(f"User {user_id} was banned in chat {chat_id}")

    except TelegramBadRequest as e:
        error_msg = f"Ошибка при блокировке: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Ban error in chat {chat_id}: {str(e)}")

@router.message(Command("unban"))
@allowed_chat_only()
async def unban_user(message: Message):
    await log_command(message)
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть использована как ответ на сообщение.")
        return

    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    # Проверка прав бота
    bot_has_rights, error_msg = await check_bot_rights(message)
    if not bot_has_rights:
        await message.reply(error_msg)
        return

    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id

    try:
        # Разблокируем пользователя
        await message.bot.unban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=True
        )

        await message.reply(
            f"Пользователь {message.reply_to_message.from_user.full_name} "
            f"(id: {user_id}) разблокирован."
        )
        logger.info(f"User {user_id} was unbanned in chat {chat_id}")

    except TelegramBadRequest as e:
        error_msg = f"Ошибка при разблокировке: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Unban error in chat {chat_id}: {str(e)}")

@router.message(Command("kick"))
@allowed_chat_only()
async def kick_user(message: Message):
    await log_command(message)
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть использована как ответ на сообщение.")
        return

    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    # Проверка прав бота
    bot_has_rights, error_msg = await check_bot_rights(message)
    if not bot_has_rights:
        await message.reply(error_msg)
        return

    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.full_name

    try:
        # Проверяем особые случаи
        if str(user_id) in settings.ADMIN_IDS.split(','):
            await message.reply("Админов кикаешь? Ай-ай-ай 😈")
            return

        # Проверяем, не пытается ли пользователь кикнуть сам себя
        if message.from_user and message.from_user.id == user_id:
            await message.reply("Нельзя кикнуть самого себя 🤪")
            return

        # Проверяем права цели
        target_member = await message.bot.get_chat_member(chat_id, user_id)
        if isinstance(target_member, (ChatMemberOwner, ChatMemberAdministrator)):
            await message.reply("Невозможно кикнуть администратора.")
            return

        # Кикаем пользователя (бан с последующим разбаном)
        await message.bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            revoke_messages=False  # Не удаляем сообщения при кике
        )
        
        # Сразу разбаниваем, чтобы пользователь мог вернуться
        await message.bot.unban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=True
        )

        await message.reply(f"Пользователь {user_name} был удален из чата.")
        logger.info(f"User {user_id} was kicked from chat {chat_id}")

    except TelegramBadRequest as e:
        error_msg = f"Ошибка при удалении пользователя: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Kick error in chat {chat_id}: {str(e)}")

@router.message(Command("warn"))
@allowed_chat_only()
async def warn_user(message: Message):
    await log_command(message)
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть использована как ответ на сообщение.")
        return

    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    # Проверка прав бота
    bot_has_rights, error_msg = await check_bot_rights(message)
    if not bot_has_rights:
        await message.reply(error_msg)
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    try:
        # Проверяем особые случаи
        if str(user_id) in settings.ADMIN_IDS.split(','):
            await message.reply("Админов предупреждаешь? Ай-ай-ай 😈")
            return

        target_member = await message.bot.get_chat_member(chat_id, user_id)
        if isinstance(target_member, (ChatMemberOwner, ChatMemberAdministrator)):
            await message.reply("Невозможно выдать предупреждение администратору.")
            return

        # Получаем или создаем запись предупреждений
        async with AsyncSessionLocal() as session:
            stmt = select(Warning).where(Warning.chat_id == chat_id, Warning.user_id == user_id)
            result = await session.execute(stmt)
            warning = result.scalars().first()

            if not warning:
                warning = Warning(chat_id=chat_id, user_id=user_id, warning_count=1, last_warning=datetime.now(timezone.utc))
                session.add(warning)
            else:
                warning.warning_count += 1
                warning.last_warning = datetime.now(timezone.utc)

            await session.commit()

        await message.reply(
            f"Пользователю {message.reply_to_message.from_user.full_name} "
            f"выдано предупреждение. Всего предупреждений: {warning.warning_count}"
        )
        logger.info(f"Warning issued to user {user_id} in chat {chat_id}")

    except Exception as e:
        error_msg = f"Ошибка при выдаче предупреждения: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Warning error in chat {chat_id}: {str(e)}")

@router.message(Command("remwarn"))
@allowed_chat_only()
async def remove_warn(message: Message, command: CommandObject):
    await log_command(message)
    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    chat_id = message.chat.id
    
    # Определяем ID пользователя из ответа на сообщение или из аргумента команды
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_name = message.reply_to_message.from_user.full_name
    elif command.args:
        try:
            user_id = int(command.args)
            try:
                member = await message.chat.get_member(user_id)
                user_name = member.user.full_name
            except:
                user_name = f"Пользователь {user_id}"
        except ValueError:
            await message.reply("Пожалуйста, укажите корректный ID пользователя.")
            return
    else:
        await message.reply(
            "Используйте команду как ответ на сообщение пользователя "
            "или укажите ID пользователя: `/remwarn <user_id>`"
        )
        return

    try:
        # Запрещаем снимать предупреждения у себя
        if message.from_user.id == user_id:
            await message.reply("Нельзя снимать предупреждения с самого себя 🤪")
            return

        async with AsyncSessionLocal() as session:
            stmt = select(Warning).where(Warning.chat_id == chat_id, Warning.user_id == user_id)
            result = await session.execute(stmt)
            warning = result.scalars().first()

            if not warning or warning.warning_count == 0:
                await message.reply(f"У пользователя нет активных предупреждений.")
                return

            warning.warning_count -= 1
            await session.commit()

        await message.reply(
            f"С пользователя {user_name} снято предупреждение. "
            f"Осталось предупреждений: {warning.warning_count}"
        )
        logger.info(f"Warning removed from user {user_id} in chat {chat_id}")

    except Exception as e:
        error_msg = f"Ошибка при снятии предупреждения: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Remove warning error in chat {chat_id}: {str(e)}")

@router.message(Command("listwarns"))
@allowed_chat_only()
async def list_warns(message: Message):
    await log_command(message)
    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    chat_id = message.chat.id

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Warning).where(Warning.chat_id == chat_id, Warning.warning_count > 0)
            result = await session.execute(stmt)
            warnings = result.scalars().all()

            if not warnings:
                await message.reply("В этом чате нет пользователей с предупреждениями.")
                return

            warn_list = []
            for warning in warnings:
                try:
                    member = await message.chat.get_member(warning.user_id)
                    user = member.user
                    user_name = f"@{user.username}" if user.username else user.full_name
                except Exception:
                    user_name = f"Пользователь {warning.user_id}"
                
                warn_list.append(f"{user_name} (ID: {warning.user_id}): {warning.warning_count} предупреждение(ий)")

            warn_list_str = "\n".join(warn_list)
            await message.reply(f"Список предупреждений:\n{warn_list_str}")
            logger.info(f"Warnings list requested in chat {chat_id}")

    except Exception as e:
        error_msg = f"Ошибка при получении списка предупреждений: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"List warnings error in chat {chat_id}: {str(e)}")

@router.message(Command("mute"))
@allowed_chat_only()
async def mute_user(message: Message, command: CommandObject):
    await log_command(message)
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть использована как ответ на сообщение.")
        return

    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    # Проверка прав бота
    bot_has_rights, error_msg = await check_bot_rights(message)
    if not bot_has_rights:
        await message.reply(error_msg)
        return

    args = command.args
    if not args:
        await message.reply("Пожалуйста, укажите время мута в минутах, например: /mute 60")
        return

    try:
        duration = int(args)
    except ValueError:
        await message.reply("Пожалуйста, укажите корректное число минут.")
        return

    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.full_name

    try:
        # Проверяем особые случаи
        if str(user_id) in settings.ADMIN_IDS.split(','):
            await message.reply("Админов мутишь? Ай-ай-ай 😈")
            return

        # Проверяем, не пытается ли пользователь замутить сам себя
        if message.from_user and message.from_user.id == user_id:
            await message.reply("Нельзя замутить самого себя 🤪")
            return

        # Проверяем права цели
        target_member = await message.bot.get_chat_member(chat_id, user_id)
        if isinstance(target_member, (ChatMemberOwner, ChatMemberAdministrator)):
            await message.reply("Невозможно замутить администратора.")
            return

        # Вычисляем время окончания мута
        until_date = datetime.now(timezone.utc) + timedelta(minutes=duration)

        # Мутим пользователя
        await message.chat.restrict(
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            ),
            until_date=until_date
        )

        await message.reply(f"Пользователь {user_name} замучен на {duration} минут.")
        logger.info(f"User {user_id} was muted in chat {chat_id} for {duration} minutes")

    except TelegramBadRequest as e:
        error_msg = f"Ошибка при муте пользователя: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Mute error in chat {chat_id}: {str(e)}")

@router.message(Command("unmute"))
@allowed_chat_only()
async def unmute_user(message: Message):
    await log_command(message)
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть использована как ответ на сообщение.")
        return

    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    # Проверка прав бота
    bot_has_rights, error_msg = await check_bot_rights(message)
    if not bot_has_rights:
        await message.reply(error_msg)
        return

    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.full_name

    try:
        # Проверяем, не пытается ли пользователь размутить сам себя
        if message.from_user and message.from_user.id == user_id:
            await message.reply("Нельзя размутить самого себя 🤪")
            return

        # Проверяем, является ли цель администратором
        if str(user_id) in settings.ADMIN_IDS.split(','):
            await message.reply("Админы не могут быть замучены 😎")
            return

        target_member = await message.bot.get_chat_member(chat_id, user_id)
        if isinstance(target_member, (ChatMemberOwner, ChatMemberAdministrator)):
            await message.reply("Администраторы не могут быть замучены.")
            return

        # Снимаем ограничения с пользователя
        await message.chat.restrict(
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )

        await message.reply(f"С пользователя {user_name} снят мут.")
        logger.info(f"User {user_id} was unmuted in chat {chat_id}")

    except TelegramBadRequest as e:
        error_msg = f"Ошибка при снятии мута: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Unmute error in chat {chat_id}: {str(e)}")

@router.message(Command("poll"))
@allowed_chat_only()
async def create_poll(message: Message, command: CommandObject):
    await log_command(message)
    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    chat_id = message.chat.id
    args = command.args

    if not args:
        await message.reply(
            "Пожалуйста, укажите вопрос и варианты ответа через '|'.\n"
            "Пример: /poll Ваш вопрос | Вариант 1 | Вариант 2"
        )
        return

    parts = [part.strip() for part in args.split('|')]
    if len(parts) < 3:  # Минимум нужен вопрос и 2 варианта ответа
        await message.reply(
            "Неверный формат. Нужно указать вопрос и минимум 2 варианта ответа.\n"
            "Пример: /poll Ваш вопрос | Вариант 1 | Вариант 2"
        )
        return

    question = parts[0]
    options = parts[1:]

    if len(options) > 10:
        await message.reply("Максимальное количество вариантов ответа - 10.")
        return

    try:
        # Отправляем опрос в чат
        await message.answer_poll(
            question=question,
            options=options,
            is_anonymous=True,
            allows_multiple_answers=False
        )
        logger.info(f"Poll created in chat {chat_id} by user {message.from_user.id}")

    except TelegramBadRequest as e:
        error_msg = f"Ошибка при создании опроса: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Poll creation error in chat {chat_id}: {str(e)}")
    except Exception as e:
        error_msg = f"Непредвиденная ошибка при создании опроса: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Unexpected poll creation error in chat {chat_id}: {str(e)}")


@router.message(Command("admin_help"))
@allowed_chat_only()
async def admin_help(message: Message):
    await log_command(message)
    # Проверка прав администратора
    is_admin, error_msg = await check_admin_rights(message)
    if not is_admin:
        await message.reply(error_msg)
        return

    help_text = """
    📚 *Команды администратора:*

    *Модерация участников:*
    • `/ban` - Забанить пользователя (навсегда)
    • `/unban` - Разбанить пользователя
    • `/kick` - Удалить пользователя из чата
    • `/mute <минуты>` - Запретить писать сообщения
    • `/unmute` - Снять ограничения на сообщения

    *Система предупреждений:*
    • `/warn` - Выдать предупреждение
    • `/remwarn` - Снять предупреждение
    • `/listwarns` - Список всех предупреждений

    *Опросы:*
    • `/poll <вопрос> | <вариант 1> | <вариант 2>` - Создать опрос
    Пример: `/poll Любите ли вы пиццу? | Да | Нет | Иногда`

    *Временные меры:*
    • `/tempban <время>` - Временно забанить пользователя

    *Статистика и информация:*
    • `/info` - Информация о пользователе
    • `/stats` - Статистика чата

    *Важные замечания:*
    • Команды бан/кик/мут/предупреждение работают только ответом на сообщение
    • Нельзя модерировать администраторов
    • Бот должен иметь права администратора
    • Максимум 10 вариантов в опросе

    Для получения подробной информации о конкретной команде используйте: `/help <команда>`
    """
    
    try:
        await message.reply(
            text=help_text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info(f"Admin help shown in chat {message.chat.id} for user {message.from_user.id}")
    except Exception as e:
        error_msg = f"Ошибка при отправке справки: {str(e)}"
        await message.reply(error_msg)
        logger.error(f"Error showing admin help in chat {message.chat.id}: {str(e)}")


@router.message(Command("info"))
@allowed_chat_only()
async def user_info(message: Message):
    await log_command(message)
    """Показывает информацию о пользователе"""
    try:
        # Проверка прав администратора
        is_admin, error_msg = await check_admin_rights(message)
        if not is_admin:
            await message.reply(error_msg)
            return
            
        # Определяем пользователя
        user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        
        # Получаем информацию о пользователе в чате
        member = await message.chat.get_member(user.id)
        
        # Получаем статистику пользователя из базы данных
        async with AsyncSessionLocal() as session:
            async with session.begin():  # Явно начинаем транзакцию
                stats = await session.execute(
                    select(UserStats)
                    .where(
                        UserStats.user_id == user.id,
                        UserStats.chat_id == message.chat.id
                    )
                )
                user_stats = stats.scalar_one_or_none()
                messages_count = user_stats.message_count if user_stats else 0
        
        # Формируем сообщение с информацией
        info = [
            "👤 <b>Информация о пользователе:</b>",
            f"ID: <code>{user.id}</code>",
            f"Имя: {user.full_name}",
            f"Статус: <code>{member.status}</code>",
            f"Бот: {'Да' if user.is_bot else 'Нет'}",
            f"Сообщений в чате: {messages_count}"
        ]
        
        # Добавляем username если есть
        if user.username:
            info.insert(3, f"Username: @{user.username}")
            
        # Добавляем язык пользователя
        if user.language_code:
            info.append(f"Язык: {user.language_code}")
            
        # Объединяем все строки
        info_text = "\n".join(info)
        
        await message.reply(info_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        await message.reply(f"Ошибка при получении информации: {str(e)}")
        

@router.message(Command("stats"))
@allowed_chat_only()
async def chat_stats(message: Message):
    await log_command(message)
    """Показывает расширенную статистику чата"""
    logger.info(f"Stats command received from user {message.from_user.id}")

    try:
        logger.info(f"Starting stats command processing for chat {message.chat.id}")

        # Проверка прав администратора
        is_admin, error_msg = await check_admin_rights(message)
        if not is_admin:
            logger.warning(f"User {message.from_user.id} tried to use stats without admin rights")
            await message.reply(error_msg)
            return

        chat = message.chat
        logger.info(f"Getting administrators for chat {chat.id}")
        admins = await message.bot.get_chat_administrators(chat.id)
        members_count = await message.bot.get_chat_member_count(chat.id)

        # Получаем статистику сообщений из базы данных
        async with AsyncSessionLocal() as session:
            logger.info("Querying database for message statistics")

            # Общее количество сообщений в чате
            total_messages_query = await session.execute(
                select(func.coalesce(func.sum(UserStats.message_count), 0))
                .where(UserStats.chat_id == chat.id)
            )
            total_messages = total_messages_query.scalar()
            logger.info(f"Total messages in chat: {total_messages}")

            # Топ 5 самых активных пользователей
            top_users_query = await session.execute(
                select(UserStats)
                .where(UserStats.chat_id == chat.id)
                .order_by(UserStats.message_count.desc())
                .limit(5)
            )
            top_users = top_users_query.scalars().all()
            logger.info(f"Found {len(top_users)} top users")

        # Формируем статистику
        stats = [
            "📊 *Общая статистика чата*",
            f"*Название:* {chat.title}",
            f"*Тип чата:* {chat.type}",
            f"*Участников:* {members_count}",
            f"*Администраторов:* {len(admins)}",
            f"*Всего сообщений:* {total_messages}",
            "",
            "👥 *Администраторы:*"
        ]

        # Добавляем список администраторов
        for admin in admins:
            admin_user = admin.user
            admin_status = "👑 Владелец" if isinstance(admin, ChatMemberOwner) else "👮 Админ"
            stats.append(f"• {admin_status}: {admin_user.full_name}")

        # Добавляем топ активных пользователей
        if top_users:
            stats.extend([
                "",
                "🏆 *Топ 5 активных участников:*"
            ])
            for i, user_stat in enumerate(top_users, 1):
                try:
                    member = await chat.get_member(user_stat.user_id)
                    user_name = member.user.full_name
                    stats.append(f"{i}. {user_name}: {user_stat.message_count} сообщ.")
                except Exception as e:
                    logger.error(f"Error getting member info: {e}")
                    stats.append(f"{i}. ID {user_stat.user_id}: {user_stat.message_count} сообщ.")

        # Добавляем описание чата если оно есть
        if chat.description:
            stats.extend([
                "",
                "*Описание чата:*",
                chat.description
            ])

        stats_text = "\n".join(stats)
        logger.info("Sending stats message")
        await message.reply(
            stats_text,
            parse_mode="Markdown"
        )
        logger.info(f"Stats successfully sent for chat {chat.id}")

    except Exception as e:
        error_msg = f"Ошибка при получении статистики: {str(e)}"
        logger.error(f"Stats error in chat {message.chat.id}: {str(e)}", exc_info=True)
        await message.reply(error_msg)

@router.message(Command("tempban"))
@allowed_chat_only()
async def temp_ban(message: Message, command: CommandObject):
    await log_command(message)
    """Временно банит пользователя с поддержкой различных форматов времени."""
    if not message.reply_to_message or not command.args:
        await message.reply("Использование: ответьте на сообщение и укажите время бана (например, 10m, 2h, 1d)")
        return

    # Функция для преобразования времени с суффиксами
    def parse_time(time_str: str) -> Optional[timedelta]:
        try:
            unit = time_str[-1].lower()
            value = int(time_str[:-1])
            if unit == 'm':
                return timedelta(minutes=value)
            elif unit == 'h':
                return timedelta(hours=value)
            elif unit == 'd':
                return timedelta(days=value)
            else:
                return None
        except (ValueError, IndexError):
            return None

    time_input = command.args.strip()
    delta = parse_time(time_input)

    if not delta:
        await message.reply("Неверный формат времени. Используйте суффиксы: m (минуты), h (часы), d (дни). Примеры: 10m, 2h, 1d")
        return

    # Ограничение максимального времени бана (например, 7 дней)
    max_delta = timedelta(days=7)
    if delta > max_delta:
        await message.reply("Максимальная продолжительность бана - 7 дней.")
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.full_name

    # Проверка, что баны не накладываются на администраторов
    admin_ids = settings.ADMIN_IDS.split(',')
    if str(user_id) in admin_ids:
        await message.reply("Невозможно забанить администратора.")
        return

    # Проверка, что бот имеет права на бан
    has_bot_rights, bot_error = await check_bot_rights(message)
    if not has_bot_rights:
        await message.reply(bot_error)
        return

    # Проверка, что пользователь имеет права администратора
    is_admin, admin_error = await check_admin_rights(message)
    if not is_admin:
        await message.reply(admin_error)
        return

    until_date = datetime.now(timezone.utc) + delta

    try:
        await message.chat.ban(
            user_id=user_id,
            until_date=until_date
        )
        await message.reply(
            f"Пользователь {user_name} забанен на {time_input}.\n"
            f"Бан истечет: {until_date.strftime('%d.%m.%Y %H:%M:%S')} UTC"
        )
        logger.info(f"User {user_id} ({user_name}) временно забанен на {time_input} в чате {message.chat.id}")
    except TelegramBadRequest as e:
        await message.reply(f"Ошибка при бане пользователя: {str(e)}")
        logger.error(f"Ошибка бана пользователя {user_id} в чате {message.chat.id}: {str(e)}")
    except Exception as e:
        await message.reply(f"Неизвестная ошибка: {str(e)}")
        logger.error(f"Неизвестная ошибка при бане пользователя {user_id} в чате {message.chat.id}: {str(e)}")


@router.message(F.text)
async def count_messages(message: Message):
    await log_command(message)
    """Подсчитывает сообщения пользователей только в определенном чате"""
    # Проверяем, что сообщение из нужного чата
    if message.chat.id != settings.CHAT_ID:
        return
        
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                stmt = select(UserStats).where(
                    UserStats.user_id == message.from_user.id,
                    UserStats.chat_id == message.chat.id
                ).with_for_update()
                
                result = await session.execute(stmt)
                user_stats = result.scalar_one_or_none()
                
                if not user_stats:
                    user_stats = UserStats(
                        user_id=message.from_user.id,
                        chat_id=message.chat.id,
                        message_count=1,
                        last_message_date=datetime.now(timezone.utc)
                    )
                    session.add(user_stats)
                else:
                    user_stats.message_count += 1
                    user_stats.last_message_date = datetime.now(timezone.utc)
                
                await session.commit()
            
    except Exception as e:
        logger.error(f"Error counting message: {e}")