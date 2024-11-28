import os
from aiogram import Router, Bot, F
from aiogram.types import Message, ChatMemberAdministrator
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Создаём объект маршрутизатора
router = Router()

# Словарь для хранения количества сообщений
message_counts = {}

@router.message(Command('report'))
async def report_user(message: Message, bot: Bot):
    """
    Обрабатывает команду /report для отправки жалобы на пользователя.

    Жалоба отправляется администраторам чата. Проверяются следующие условия:
    - Команда должна быть ответом на сообщение.
    - Пользователь не может пожаловаться на себя.
    - Репорт на администраторов запрещён.
    - Репорт на сообщения от групповых аккаунтов (каналов) также запрещён.

    Args:
        message (Message): Сообщение с командой.
        bot (Bot): Объект бота для отправки сообщений.
    """
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть ответом на какое-либо сообщение!")
        return

    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.reply("Нельзя репортить самого себя 🤪")
        return

    user_id = message.reply_to_message.from_user.id
    name = message.reply_to_message.from_user.username or message.reply_to_message.from_user.first_name

    # Проверяем, является ли пользователь администратором
    admins = os.getenv('ADMIN_IDS')
    admins_list = [int(number.strip()) for number in admins.split(',')]
    if user_id in admins_list:
        await message.reply("Админов репортишь? Ай-ай-ай 😈")
        return

    if message.reply_to_message.from_user.id == os.getenv('CHANNEL_ID'):
        await message.delete()
        return

    username = message.from_user.username or message.from_user.first_name
    text = f"Пользователь {username} отправил репорт на {name}!"
    chat_id = int(os.getenv('SHARECHAT_ID'))

    try:
        await bot.send_message(chat_id=chat_id, text=text)
        await message.reply(f"Репорт на {name} успешно отправлен!")
    except Exception as e:
        print(f"Ошибка при пересылке сообщения: {e}")
        await message.answer("Произошла ошибка при пересылке сообщения.")


@router.message(Command('help'))
async def cmd_help(message: Message):
    """
    Отправляет список доступных команд в зависимости от прав пользователя.

    Если пользователь является администратором, список включает команды для модерации.
    В противном случае отображается базовый набор команд.

    Args:
        message (Message): Сообщение с командой.
    """
    chat_id = message.chat.id
    member = await message.bot.get_chat_member(chat_id, message.from_user.id)

    if not isinstance(member, ChatMemberAdministrator) or not member.can_restrict_members:
        text = (
            "Список доступных команд:\n"
            "*/avatar* - Посмотреть свой аватар.\n"
            "*/help* - Помощь по командам.\n"
            "*/info* - Информация о боте.\n"
            "*/report* - Пожаловаться на участника.\n"
            "*/rules* - Показать правила чата.\n"
            "*/stats* - Статистика чата.\n"
            "@admin - Вызвать админа."
        )
        await message.reply(text, parse_mode='Markdown')
        return

    text = (
        "Список доступных команд:\n"
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
        "*/unmute* - Размутить участника.\n"
        "*/warn* - Выдать предупреждение.\n"
        "@admin - Вызвать админа."
    )
    await message.reply(text, parse_mode='Markdown')


@router.message(Command('info'))
async def cmd_info(message: Message):
    """
    Отправляет информацию о боте, включая ссылку на его исходный код.

    Args:
        message (Message): Сообщение с командой.
    """
    await message.answer(
        "Я <b>Бот</b> помощник для ТГ канала <b>Вольт</b>. "
        "Он <b>написал</b> меня для помощи в чате.\n"
        "<i>Вот мой исходный код:</i> <a href='https://github.com/V0L1ER/VoltChatHelperBot.git'><b>Гитхаб</b></a>",
        parse_mode='HTML',
        disable_web_page_preview=True
    )


@router.message(Command("avatar"))
async def send_avatar(message: Message):
    """
    Отправляет аватар пользователя, отправившего команду.

    Если у пользователя нет аватара, бот уведомляет об этом.

    Args:
        message (Message): Сообщение с командой.
    """
    user_photos = await message.from_user.get_profile_photos()

    if not user_photos or user_photos.total_count == 0:
        await message.reply("У вас нет аватара!")
        return

    photo = user_photos.photos[0][-1]  # Берём фото самого высокого качества
    await message.reply_photo(photo.file_id)
    
    
@router.message(Command("rules"))
async def rules_command(message: Message):
    """
    Отправляет правила чата.

    Args:
        message (Message): Сообщение с командой.
    """
    rules_text = ("Правила Чата Айтишников\n"
        "*[1]* Запрещено быть тупым.\n\n"
        "*[2]* Запрещен спам и бессмысленный флуд, разбитие мыслей на множество мелких сообщений, оффтоп стикерами, видосами, картинками, текстами.\n\n"
        "*[3]* Запрещена политика.\n"
        "_❕Гитлеры, Сталины, свастика, 1488 и прочие 'пасхалки' тоже считается за политику, за что тоже можно получить бан._\n\n"
        "*[4]* Запрещены любые срачи и агрессивные конфликты на любые темы. Спокойные дискуссии за срач не считаются. Просим вас решать разногласия в личных сообщениях, не впутывая третьих лиц.\n"
        "_❕Вмешиваясь, вы тоже становитесь причастными и можете попасть под бан._\n\n"
        "*[5]* Запрещён NSFW: 18+, порнография, эротика, расчленёнка, жестокость, шок–контент, суицид (и всё что об этом напоминает), кадры увечий – в любых возможных видах и проявлениях, а также публикация всякого рода контента или обсуждение на темы: наркотиков, терроризма, бедствий, катастроф, катаклизмов, милитари, и прочее подобное, включая что–либо связанное с чем–то что Not Suitable for Work or Situation, or for this Group (Англ.)\n\n"
        "*[6]* Запрещен слив любой личной информации любого другого человека: Номера, адреса, данные карт, переписки, скриншоты и любая другая информация, которая не согласована с её владельцем, и если её публикация может причинить вред как моральный, так и физический, а также деаноны/доксинг.\n"
        "_❕Запрещен слив платного контента других авторов (Boosty, Patreon, приватки и т.д.) и всего того что не предназначено для широкой аудитории._\n\n"
        "*[7]* Запрещены пиар/реклама. Пиар в никнейме, на аватарке. Реклама и пиар любых каналов, проектов, групп, организаций или сообществ, никак не связанных с Вольтом. Любые действия в целях личной выгоды, ради продвижения, любая продажа и попрошайничество.\n\n"
        "*[8]* Запрещено выдавать себя за другого человека если вы таковыми не являетесь. Ставить чужие имена, псевдонимы, притворяться другой персоной или администрацией.\n\n"
        "*[9]* Запрещён обход блокировок (бан/мут) и вступление в группу с альтернативных аккаунтов.\n\n"
        "*[11]* Запрещено нарушать правила и неприлично вести себя в видеочате.\n\n"
        "*ДОПОЛНЕНИЕ:*\n"
        "Вы можете получить перманетный бан по любому из правил, или по решению администрации в случае такой необходимости, так что будьте взаимовежливы.\n"
        "Видите неадеквата? – Забейте на него… Или репортите, желательно обьяснив что не так. Команда – /report.\n"
        "❕Строго запрещено использовать репорт как инструмент наивного жалобничества, иначе вы будете забанены.\n"
    )
    await message.reply(rules_text, parse_mode='Markdown')
    
@router.message(F.text.contains('@admin'))
async def calling_all_admin(message: Message, bot: Bot):
    """
    Уведомляет администраторов о запросе помощи.

    Если команда отправлена в ответ на сообщение, генерируется ссылка на сообщение.

    Args:
        message (Message): Сообщение с упоминанием администраторов.
        bot (Bot): Объект бота для отправки уведомлений.
    """
    if not message.reply_to_message:
        username = message.from_user.username or message.from_user.first_name
        text = f"Пользователь {username} вызывает администраторов!"
        chat_id = int(os.getenv('SHARECHAT_ID'))

        try:
            await bot.send_message(chat_id=chat_id, text=text)
            await message.reply("У админов перекур, скоро придут)")
        except Exception as e:
            print(f"Ошибка при пересылке сообщения: {e}")
            await message.answer("Произошла ошибка при пересылке сообщения.")
        return

    chat_id = message.chat.id
    msg_id = message.reply_to_message.message_id
    chat_id_link = str(chat_id).replace('-100', '')

    text = (
        "Товарищи админы, в чате нужно ваше присутствие!\n\n"
        f'<a href="https://t.me/c/{chat_id_link}/{msg_id}">Перейти к сообщению</a>'
    )
    await message.answer(text, parse_mode='HTML')
        
        
# Словарь для хранения статистики сообщений
# Структура: {chat_id: {user_id: count}}, где:
# - chat_id: ID чата
# - user_id: ID пользователя
# - count: количество сообщений
message_counts = {}


@router.message(Command("stats"))
async def chat_stats(message: Message):
    """
    Команда для отображения статистики сообщений в чате.

    Формирует список топ-10 самых активных пользователей в чате на основе количества
    отправленных сообщений. Если статистика недоступна, отправляет соответствующее уведомление.

    Args:
        message (Message): Сообщение с командой /stats.
    """
    chat_id = message.chat.id

    # Проверяем, есть ли статистика для текущего чата
    if chat_id not in message_counts or not message_counts[chat_id]:
        await message.reply("Статистика пока недоступна.")
        return

    # Сортируем пользователей по количеству сообщений в порядке убывания
    sorted_users = sorted(message_counts[chat_id].items(), key=lambda x: x[1], reverse=True)

    # Ограничиваем список до топ-10 пользователей
    top_users = sorted_users[:10]

    # Формируем текст сообщения со статистикой
    stats_text = "📊 <b>Статистика чата — Топ 10 активных пользователей:</b>\n\n"
    for user_id, msg_count in top_users:
        try:
            # Получаем информацию о пользователе из чата
            user = await message.chat.get_member(user_id)
            if user.user.username:  # Если у пользователя есть username
                user_name = f"@{user.user.username}"
            else:  # Если username отсутствует, используем полное имя
                user_name = user.user.full_name
        except Exception:
            # Если не удалось получить данные о пользователе
            user_name = "Неизвестный пользователь"

        # Добавляем строку с информацией о пользователе и его активности
        stats_text += f"{user_name}: {msg_count} сообщений\n"

    # Отправляем текст статистики
    await message.reply(stats_text, parse_mode='HTML')


@router.message()
async def count_messages(message: Message):
    """
    Подсчитывает количество сообщений, отправленных пользователями в чате.

    Каждое сообщение увеличивает соответствующий счётчик в словаре message_counts.

    Args:
        message (Message): Сообщение, отправленное в чате.
    """
    chat_id = message.chat.id  # ID чата, в котором было отправлено сообщение
    user_id = message.from_user.id  # ID пользователя, отправившего сообщение

    # Инициализируем словарь для чата, если его ещё нет
    if chat_id not in message_counts:
        message_counts[chat_id] = {}

    # Инициализируем счётчик для пользователя, если его ещё нет
    if user_id not in message_counts[chat_id]:
        message_counts[chat_id][user_id] = 0

    # Увеличиваем счётчик сообщений пользователя
    message_counts[chat_id][user_id] += 1
    
    
    