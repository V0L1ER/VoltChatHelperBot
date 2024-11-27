import os

from aiogram import Router, Bot, F
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

router = Router()

@router.message()
async def handle_messages(message: Message):
    if message.chat.type == 'private':
        await message.reply("Я бот для чата Вольта")
