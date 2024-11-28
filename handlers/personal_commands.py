import os

from aiogram import Router, Bot, F
from aiogram.types import Message, ChatMemberUpdated
from dotenv import load_dotenv

load_dotenv()

router = Router()

@router.message()
async def handle_messages(message: Message):
    if message.chat.type == 'private':
        await message.reply("Я бот для чата Вольта")
        
@router.chat_member()
async def welcome_new_member(event: ChatMemberUpdated):
    new_member = event.new_chat_member
    if new_member.status == "member":
        user = new_member.user
        await event.bot.send_message(
            event.chat.id,
            f"Добро пожаловать, {user.full_name}! Пожалуйста, ознакомьтесь с правилами чата."
        )
