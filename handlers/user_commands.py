import os

from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()


router = Router()

@router.message(Command('report'))
async def report_user(message: Message, bot: Bot):
    
    # Проверяет, является ли команда ответом на сообщение
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть ответом на какое-либо сообщение!")
        return

    # Проверяет, если команда использована на себя
    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.reply("Нельзя репортить самого себя 🤪")
        return

    # Проверяет, если репорт на админа
    user_id = message.reply_to_message.from_user.id  # Получаем ID пользователя, на которого направлен репорт
    name = message.reply_to_message.from_user.username or message.reply_to_message.from_user.first_name
    admins = os.getenv('ADMIN_IDS')
    admins_list = [int(number.strip()) for number in admins.split(',')]
    if user_id in admins_list:
        await message.reply("Админов репортишь? Ай-ай-ай 😈")
        return

    # Проверяет, если репорт на сообщение от группы
    if message.reply_to_message.from_user.id == os.getenv('CHANNEL_ID'):
        await message.delete()
        return

    username = message.from_user.username or message.from_user.first_name
    text = f"Пользователь {username} отправил репорт на {name}!"
    chat_id = os.getenv('SHARECHAT_ID')
    chat_id = int(chat_id)
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text
        )
        await message.reply(f"Репорт на {name} успешно отправлен!")
    except Exception as e:
        print(f"Ошибка при пересылке сообщения: {e}")
        await message.answer("Произошла ошибка при пересылке сообщения.")
        
        
@router.message(Command('help'))
async def cmd_help(message: Message):
    text = """avatar - Посмотреть свой аватар.
    \nban - Заблокировать участника.
    \nhelp - Помощь по командам.
    \ninfo - Информация о боте.
    \nkick - Выгнать участника.
    \nlistwarns - Список предупреждений.
    \nremwarn - Удалить предупреждение.
    \nreport - Пожаловаться на участника.
    \nunban - Разблокировать участника.
    \nwarn - Выдать предупреждение.
        """
    await message.answer(text)

@router.message(Command('info'))
async def cmd_info(message: Message):
    await message.answer("Я Бот помощник для ТГ канала Вольта. Он написал меня для помощи в чате. Вот мой исходный код: <a href='https://t.me/c/{chat_id_link}/{msg_id}'>Перейти к сообщению</a>")

@router.message(Command("avatar"))
async def send_avatar(message: Message):
    # Получаем фотографии профиля пользователя
    user_photos = await message.from_user.get_profile_photos()

    # Проверяем, есть ли у пользователя аватары
    if not user_photos or user_photos.total_count == 0:
        await message.reply("У вас нет аватара!")
        return

    # Берём первую фотографию профиля (самая последняя загруженная)
    photo = user_photos.photos[0][-1]  # Берём фото самого высокого качества

    # Отправляем фотографию в ответ
    await message.reply_photo(photo.file_id)
    
@router.message(F.text.contains('@admin'))
async def calling_all_admin(message: Message, bot: Bot):
    if not message.reply_to_message:
        username = message.from_user.username or message.from_user.first_name
        text = f"Пользователь {username} вызывает администраторов!"
        chat_id = os.getenv('SHARECHAT_ID')
        chat_id = int(chat_id)
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text
            )
            await message.reply("У админов перекур, скоро прийдут)")
        except Exception as e:
            print(f"Ошибка при пересылке сообщения: {e}")
            await message.answer("Произошла ошибка при пересылке сообщения.")
        return
    else:
        chat_id = message.chat.id
        msg_id = message.reply_to_message.message_id

        # Убираем префикс '-100' из chat_id для формирования корректной ссылки
        chat_id_link = str(chat_id).replace('-100', '')

        text = (
            "Товарищи админы, в чате нужно ваше присутствие!\n\n"
            f'<a href="https://t.me/c/{chat_id_link}/{msg_id}">Перейти к сообщению</a>'
        )
        await message.answer(text, parse_mode='HTML')
        
    
        
    
    
    
    