from aiogram.types import Message
from utils.logger import BotLogger

logger = BotLogger.get_logger()

async def log_command(message: Message):
    logger.info(f"Command {message.text} used by user {message.from_user.id} in chat {message.chat.id}")

