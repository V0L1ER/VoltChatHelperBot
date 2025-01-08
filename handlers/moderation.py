from aiogram import Router
from aiogram.types import Message
from filters.bad_word_filters import ContainsForbiddenWord
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from database.database import AsyncSessionLocal
from database.models import Warning
from datetime import datetime, timezone
from utils.logger import BotLogger
from middlewares.spam_filter import SpamFilter
import asyncio
from config import get_settings

router = Router()

logger = BotLogger.get_logger()
settings = get_settings()

WARN_LIMIT = 3  # Лимит предупреждений

# Добавляем в начало файла
spam_filter = SpamFilter()

@router.message(ContainsForbiddenWord())
async def handle_forbidden_words(message: Message):
    logger.info(f"Deleted message with forbidden words from user {message.from_user.id} in chat {message.chat.id}")
    await message.delete()
    chat_id = message.chat.id
    user_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(Warning).where(Warning.chat_id == chat_id, Warning.user_id == user_id)
        result = await session.execute(stmt)
        warning = result.scalars().first()

        if warning:
            current_warnings = warning.warning_count
            warning.warning_count += 1
            warning.last_warning = datetime.now(timezone.utc)
        else:
            warning = Warning(
                chat_id=chat_id,
                user_id=user_id,
                warning_count=1,
                last_warning=datetime.now(timezone.utc)
            )
            session.add(warning)
            current_warnings = 1

        await session.commit()

        if warning.warning_count >= WARN_LIMIT:
            try:
                await message.chat.ban(user_id)
                await message.answer(f"Пользователь {message.from_user.full_name} был исключен из чата за превышение лимита предупреждений ({WARN_LIMIT}).")
                await message.chat.unban(user_id)
                # Сброс предупреждений после исключения
                await session.delete(warning)
                await session.commit()
            except Exception as e:
                await message.answer(f"Не удалось исключить пользователя: {e}")
        else:
            await message.answer(f"Сообщение с запрещёнными словами было удалено. Предупреждение {warning.warning_count}/{WARN_LIMIT}.")  

# @router.message(spam_filter)
async def handle_spam(message: Message, spam_type: str, time_window: float = None):
    try:
        # Удаляем сообщение
        await message.delete()
        
        # Формируем текст предупреждения
        warning_text = {
            "frequency": f"⚠️ Слишком много сообщений за {time_window:.1f} секунд!",
            "repeat": "⚠️ Прекратите отправлять одинаковые сообщения!",
            "flood": "⚠️ Прекратите флудить короткими сообщениями!",
            "caps": "⚠️ Не пишите КАПСОМ!",
            "urls": "⚠️ Слишком много ссылок в сообщении!"
        }.get(spam_type, "⚠️ Обнаружен спам!")

        # Отправляем предупреждение
        warn_msg = await message.answer(
            f"{warning_text}\n"
            f"👤 Пользователь: {message.from_user.mention_html()}"
        )
        
        # Удаляем предупреждение через некоторое время
        await asyncio.sleep(settings.MESSAGE_DELETION_DELAY)
        await warn_msg.delete()
        
        logger.info(
            f"Spam detected from user {message.from_user.id}, "
            f"type: {spam_type}, chat: {message.chat.id}"
        )
        
    except Exception as e:
        logger.error(f"Error handling spam message: {e}", exc_info=True)  
