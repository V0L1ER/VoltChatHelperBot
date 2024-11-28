import os

from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberAdministrator
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
    
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)
    
    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        text = ("Список доступных команд:\n"
            "*/avatar* - Посмотреть свой аватар.\n"
            "*/help* - Помощь по командам.\n"
            "*/info* - Информация о боте.\n"
            "*/report* - Пожаловаться на участника.\n"
            "*/rules* - Показать правила чата\n"
            "*/stats* - Статистика чата.\n"
            "@admin - Вызвать админа"
            )
        await message.reply(text, parse_mode='Markdown')
        return
    
    
    text = ("Список доступных команд:\n"
            "*/avatar* - Посмотреть свой аватар.\n"
            "*/ban* - Заблокировать участника.\n"
            "*/help* - Помощь по командам.\n"
            "*/info* - Информация о боте.\n"
            "*/kick* - Выгнать участника.\n"
            "*/listwarns* - Список предупреждений.\n"
            "*/mute* - Замутить участника.\n"
            "*/poll* - Создать опрос.\n"
            "*/remwarn* - Удалить предупреждение.\n"
            "*/report* - Пожаловаться на участника.\n"
            "*/rules* - Показать правила чата.\n"
            "*/stats* - Статистика чата.\n"
            "*/unban* - Разблокировать участника.\n"
            "*/unmute* - размутить участника.\n"
            "*/warn* - Выдать предупреждение.\n"
            "@admin - Вызвать админа"
            )
    await message.reply(text, parse_mode='Markdown')
    
    
message_counts = {}

@router.message(Command('info'))
async def cmd_info(message: Message):
    await message.answer("Я <b>Бот</b> помощник для ТГ канала <b>Вольт</b>. Он <b>написал</b> меня для помощи в чате.\n<i>Вот мой исходный код:</i> <a href='https://github.com/V0L1ER/VoltChatHelperBot.git'><b>Гитхаб<b/></a>", parse_mode='HTML', disable_web_page_preview=True)

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
    
    
@router.message(Command("rules"))
async def rules_command(message: Message):
    rules_text = (
        "Правила чата:\n"
        "1. Уважайте других участников.\n"
        "2. Не спамьте и не флудите.\n"
        "3. Запрещена реклама без согласования с администрацией.\n"
        "4. Соблюдайте тематику чата.\n"
        "5. Запрещены оскорбления и нецензурная лексика."
    )
    await message.reply(rules_text)
    
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
        
        
message_counts = {}


@router.message(Command("stats"))
async def chat_stats(message: Message):
    chat_id = message.chat.id

    if chat_id not in message_counts or not message_counts[chat_id]:
        await message.reply("Статистика пока недоступна.")
        return

    # Сортируем пользователей по количеству сообщений
    sorted_users = sorted(message_counts[chat_id].items(), key=lambda x: x[1], reverse=True)

    # Ограничиваем до топ-10
    top_users = sorted_users[:10]

    stats_text = "📊 <b>Статистика чата — Топ 10 активных пользователей:</b>\n\n"
    for user_id, msg_count in top_users:
        try:
            user = await message.chat.get_member(user_id)
            if user.user.username:
                user_name = f"@{user.user.username}"
            else:
                user_name = user.user.full_name
        except Exception:
            user_name = "Неизвестный пользователь"

        stats_text += f"{user_name}: {msg_count} сообщений\n"

    await message.reply(stats_text, parse_mode='HTML')
        
@router.message()
async def count_messages(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Инициализируем словарь для чата, если его ещё нет
    if chat_id not in message_counts:
        message_counts[chat_id] = {}

    # Инициализируем счётчик для пользователя
    if user_id not in message_counts[chat_id]:
        message_counts[chat_id][user_id] = 0

    # Увеличиваем счётчик сообщений
    message_counts[chat_id][user_id] += 1
    
    
    