from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command
from utils.logger import BotLogger
from config import get_settings
import time
import psutil
import platform
from datetime import datetime
from sqlalchemy import select, func
from database.models import UserStats
from database.database import AsyncSessionLocal
import html
from utils.command_logging import log_command
router = Router()
logger = BotLogger.get_logger()
settings = get_settings()

from functools import wraps

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

@router.message(Command("report"))
@allowed_chat_only()
async def report_user(message: Message, bot: Bot):
    await log_command(message)
    """
    Обрабатывает команду /report для отправки жалобы на пользователя.
    """
    try:
        logger.info(f"Команда /report вызвана пользователем {message.from_user.id}")

        # Проверка наличия ответа на сообщение
        if not message.reply_to_message:
            logger.warning(f"Команда /report использована без ответа на сообщение пользователем {message.from_user.id}")
            await message.reply("Эта команда должна быть ответом на какое-либо сообщение!")
            return

        # Проверка на самореппорт
        if message.reply_to_message.from_user.id == message.from_user.id:
            logger.warning(f"Пользователь {message.from_user.id} пытается отправить репорт на себя")
            await message.reply("Нельзя репортить самого себя 🤪")
            return

        reported_user = message.reply_to_message.from_user
        reporter = message.from_user

        # Проверка на админа из конфига и на админа чата
        try:
            chat_member = await bot.get_chat_member(message.chat.id, reported_user.id)
            is_admin = (
                reported_user.id in settings.admin_ids_list or 
                chat_member.status in ['administrator', 'creator']
            )
            
            if is_admin:
                logger.warning(f"Пользователь {reporter.id} пытается отправить репорт на админа {reported_user.id}")
                await message.reply("Админов репортишь? Ай-ай-ай 😈")
                return
                
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса администратора: {e}", exc_info=True)
            # Продолжаем выполнение, если не удалось проверить статус админа

        # Проверка на канал
        if reported_user.id == settings.CHANNEL_ID:
            logger.warning(f"Пользователь {reporter.id} пытается отправить репорт на канал")
            await message.delete()
            return

        # Формирование текста репорта
        reporter_name = reporter.username or reporter.first_name
        reported_name = reported_user.username or reported_user.first_name
        
        report_text = (
            f"📣 *Новый репорт*\n\n"
            f"🔸 *От:* {reporter_name} (ID: {reporter.id})\n"
            f"🔸 *На:* {reported_name} (ID: {reported_user.id})"
        )

        # Отправка репорта
        try:
            await bot.send_message(
                chat_id=settings.SHARECHAT_ID,
                text=report_text,
                parse_mode="Markdown"
            )
            logger.info(f"Репорт успешно отправлен от {reporter.id} на {reported_user.id}")
            await message.reply(f"Репорт на {reported_name} успешно отправлен!")
            
        except Exception as e:
            error_msg = f"Не удалось отправить репорт: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await message.reply("Произошла ошибка при отправке репорта.")
            
    except Exception as e:
        logger.error(f"Общая ошибка в команде report: {str(e)}", exc_info=True)
        await message.reply("Произошла ошибка при обработке команды.") 
             
@router.message(Command("about"))
@allowed_chat_only()
async def about_bot(message: Message):
    await log_command(message)
    """
    Отправляет расширенную информацию о боте, включая версию, автора и ссылку на исходный код.
    """
    try:
        logger.info(f"Команда /about вызвана пользователем {message.from_user.id}")
        
        # Пытаемся прочитать кастомный текст
        try:
            with open('data/about_text.txt', 'r', encoding='utf-8') as f:
                about_text = f.read()
        except FileNotFoundError:
            # Используем текст по умолчанию, если файл не найден
            bot_version = "1.0.0"
            about_text = (
                f"🤖 <b>VoltChatHelper Bot v{bot_version}</b>\n\n"
                "📝 <b>О боте:</b>\n"
                "Я умный помощник для чата канала <b>Вольта</b>. "
                "Помогаю модерировать чат и делаю общение удобнее.\n\n"
                "🛠 <b>Возможности:</b>\n"
                "• Модерация сообщений\n"
                "• Система репортов\n"
                "• Автоматические приветствия\n"
                "• И многое другое!\n\n"
                "👨‍💻 <b>Разработчик:</b> @V0L1ER\n"
                "🔗 <b>Исходный код:</b> <a href='https://github.com/V0L1ER/VoltChatHelperBot'>GitHub</a>\n\n"
                "💡 Используйте /help для просмотра списка команд"
            )
        
        await message.answer(
            about_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        logger.info(f"Расширенная информация о боте отправлена пользователю {message.from_user.id}")
        
    except Exception as e:
        error_msg = "Произошла ошибка при отправке информации о боте"
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        await message.reply(error_msg)

@router.message(Command("avatar"))
@allowed_chat_only()
async def send_avatar(message: Message):
    await log_command(message)
    """
    Отправляет аватар пользователя. Может отправить как свой аватар,
    так и аватар другого пользователя при ответе на его сообщение.
    """
    try:
        logger.info(f"Команда /avatar вызвана пользователем {message.from_user.id}")
        
        # Определяем целевого пользователя (автор сообщения или тот, кому ответили)
        target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        user_name = target_user.username or target_user.first_name
        
        try:
            user_photos = await target_user.get_profile_photos()
            
            if not user_photos or user_photos.total_count == 0:
                logger.info(f"У пользователя {target_user.id} нет аватара")
                await message.reply(
                    f"{'У вас' if target_user.id == message.from_user.id else f'У пользователя {user_name}'} "
                    "нет аватара! 🤷‍♂️"
                )
                return
            
            # Отправляем фото с информацией
            photo = user_photos.photos[0][-1]  # Берём последнее фото максимального размера
            caption = (
                f"🖼 Аватар {'вашего' if target_user.id == message.from_user.id else 'пользователя'} "
                f"профиля\n"
                f"👤 Пользователь: {user_name}\n"
                f"📊 Всего аватаров: {user_photos.total_count}"
            )
            
            await message.reply_photo(
                photo.file_id,
                caption=caption
            )
            logger.info(f"Аватар успешно отправлен для пользователя {target_user.id}")
            
        except Exception as e:
            logger.error(f"Ошибка при получении фото профиля: {str(e)}", exc_info=True)
            await message.reply("Не удалось получить аватар 😢")
            
    except Exception as e:
        logger.error(f"Общая ошибка в команде avatar: {str(e)}", exc_info=True)
        await message.reply("Произошла ошибка при обработке команды 😔")

@router.message(Command("rules"))
@allowed_chat_only()
async def rules_command(message: Message):
    await log_command(message)
    """
    Отправляет правила чата с форматированием и обработкой ошибок.
    """
    try:
        logger.info(f"Команда /rules вызвана пользователем {message.from_user.id}")
        
        rules_text = (
            "📜 *ПРАВИЛА ЧАТА АЙТИШНИКОВ*\n\n"
            "🚫 *1. Запрещено быть тупым*\n\n"
            "🚫 *2. Запрещены спам и флуд*\n"
            "• Разбитие мыслей на множество мелких сообщений\n"
            "• Оффтоп стикерами, видео, картинками, текстами\n\n"
            "🚫 *3. Запрещена политика*\n"
            "_❗️ Включая исторические отсылки, символику и 'пасхалки'_\n\n"
            "🚫 *4. Запрещены срачи и конфликты*\n"
            "• Конструктивные дискуссии разрешены\n"
            "_❗️ Решайте разногласия в личных сообщениях_\n\n"
            "🔞 *5. Запрещён NSFW-контент*\n"
            "• Контент 18+, порнография, эротика\n"
            "• Жестокость, шок-контент, расчленёнка\n"
            "• Обсуждение наркотиков, терроризма, катастроф\n\n"
            "🔒 *6. Запрещен слив личной информации*\n"
            "• Номера, адреса, данные карт, переписки\n"
            "• Деанон/доксинг в любом виде\n"
            "_❗️ Запрещен слив платного контента (Boosty, Patreon и др.)_\n\n"
            "📢 *7. Запрещена реклама*\n"
            "• Пиар в никнейме или на аватарке\n"
            "• Реклама сторонних проектов\n"
            "• Попрошайничество и действия для личной выгоды\n\n"
            "🎭 *8. Запрещена имитация других лиц*\n"
            "• Использование чужих имён\n"
            "• Имитация администрации\n\n"
            "⛔️ *9. Запрещен обход блокировок*\n"
            "• Использование альтернативных аккаунтов\n\n"
            "📹 *10. Запрещено нарушать правила видеочата*\n\n"
            "⚠️ *ВАЖНО:*\n"
            "• За любое нарушение может быть выдан перманентный бан\n"
            "• Используйте /report для жалоб на нарушителей\n"
            "_❗️ Злоупотребление репортами карается баном_\n\n"
            "👮‍♂️ Администрация оставляет за собой право на окончательное решение в спорных ситуациях."
        )
        
        await message.reply(
            rules_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        logger.info(f"Правила успешно отправлены пользователю {message.from_user.id}")
        
    except Exception as e:
        error_msg = "Произошла ошибка при отправке правил"
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        await message.reply(f"{error_msg}. Пожалуйста, попробуйте позже.")

@router.message(Command("admin"))
@allowed_chat_only()
async def calling_all_admin(message: Message, bot: Bot):
    await log_command(message)
    """
    Уведомляет администраторов о запросе помощи.
    При ответе на сообщение создаёт ссылку на проблемное сообщение.
    """
    try:
        logger.info(f"Команда /admin вызвана пользователем {message.from_user.id}")
        
        username = message.from_user.username or message.from_user.first_name
        
        # Проверка таймаута между вызовами админов (например, 5 минут)
        # Здесь можно добавить проверку через Redis или другое хранилище
        
        if message.reply_to_message:
            # Если команда отправлена в ответ на сообщение
            chat_id = message.chat.id
            msg_id = message.reply_to_message.message_id
            chat_id_link = str(chat_id).replace('-100', '')
            
            admin_text = (
                f"⚠️ <b>Требуется внимание администрации!</b>\n\n"
                f"👤 Вызвал: {username}\n"
                f"💬 Чат: {message.chat.title}\n"
                f"🔗 <a href='https://t.me/c/{chat_id_link}/{msg_id}'>Перейти к сообщению</a>"
            )
            
            user_text = (
                "✅ Администраторы уведомлены!\n"
                "⏳ Пожалуйста, подождите, скоро кто-нибудь подойдет."
            )
        else:
            # Если команда отправлена без ответа на сообщение
            admin_text = (
                f"⚠️ <b>Вызов администрации</b>\n\n"
                f"👤 Пользователь: {username}\n"
                f"💬 Чат: {message.chat.title}\n"
                f"⏰ Время: {message.date.strftime('%H:%M:%S')}"
            )
            
            user_text = "✅ Администраторы уведомлены о вашем запросе!"

        # Отправка уведомления администраторам
        try:
            await bot.send_message(
                chat_id=settings.SHARECHAT_ID,
                text=admin_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            # Отправка подтверждения пользователю
            await message.reply(user_text)
            
            logger.info(f"Уведомление админов успешно отправлено от пользователя {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления админам: {str(e)}", exc_info=True)
            await message.reply(
                "😔 Произошла ошибка при уведомлении администраторов.\n"
                "Пожалуйста, попробуйте позже."
            )
            
    except Exception as e:
        logger.error(f"Общая ошибка в команде admin: {str(e)}", exc_info=True)
        await message.reply("❌ Произошла ошибка при обработке команды.")

@router.message(Command("help"))
@allowed_chat_only()
async def help_command(message: Message):
    await log_command(message)
    """
    Отправляет список доступных команд с их описанием.
    """
    try:
        logger.info(f"Команда /help вызвана пользователем {message.from_user.id}")
        
        help_text = (
            "🤖 *Доступные команды:*\n\n"
            "👥 *Основные команды:*\n"
            "• <code>/help</code> - Показать это сообщение\n"
            "• <code>/about</code> - Информация о боте\n"
            "• <code>/rules</code> - Правила чата\n"
            "• <code>/ping</code> - Проверка работы бота\n\n"
            
            "👤 *Команды профиля:*\n"
            "• <code>/avatar</code> - Показать аватар (свой или ответом на сообщение)\n"
            "• <code>/profile</code> - Информация о профиле\n"
            "• <code>/top</code> - Топ активных пользователей\n\n"
            
            "🛡 *Модерация:*\n"
            "• <code>/report</code> - Пожаловаться на сообщение (ответом)\n"
            "• <code>/admin</code> - Вызвать администратора\n\n"
            
            "💡 *Как использовать:*\n"
            "• Для команд с ответом, отвечайте на сообщение\n"
            "• Пример: ответьте на сообщение командой /report\n\n"
            
            "⚠️ *Примечание:*\n"
            "• Не злоупотребляйте командами\n"
            "• За спам командами последует ограничение\n"
            "• При проблемах обратитесь к администраторам"
        )
        
        await message.reply(
            help_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        logger.info(f"Справка успешно отправлена пользователю {message.from_user.id}")
        
    except Exception as e:
        error_msg = "Произошла ошибка при отправке справки"
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        await message.reply(f"{error_msg}. Пожалуйста, попробуйте позже.")

@router.message(Command("ping"))
@allowed_chat_only()
async def ping_command(message: Message):
    await log_command(message)
    """
    Проверяет работоспособность бота и показывает системную информацию.
    """
    try:
        logger.info(f"Команда /ping вызвана пользователем {message.from_user.id}")
        
        # Замеряем время ответа
        start = time.perf_counter()
        ping_msg = await message.reply("🔄 Проверка соединения...")
        end = time.perf_counter()
        
        # Получаем информацию о системе
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024
        cpu_usage = psutil.cpu_percent()
        
        # Форматируем время работы бота
        start_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_text = (
            "🏓 Понг!\n\n"
            f"⏱ Задержка: <code>{(end - start) * 1000:.1f} мс</code>\n"
            f"🔌 Соединение: <code>Стабильное</code>\n"
            f"⌛️ Аптайм: <code>{hours:02d}:{minutes:02d}:{seconds:02d}</code>\n\n"
            "📊 Системная информация:\n"
            f"💾 RAM: <code>{memory_usage:.1f} MB</code>\n"
            f"💻 CPU: <code>{cpu_usage}%</code>\n"
            f"🖥 OS: <code>{platform.system()}</code>\n"
            f"🐍 Python: <code>{platform.python_version()}</code>"
        )
        
        await ping_msg.edit_text(
            status_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        logger.info(
            f"Ping выполнен успешно. "
            f"Задержка: {(end - start) * 1000:.1f}мс, "
            f"RAM: {memory_usage:.1f}MB, "
            f"CPU: {cpu_usage}%"
        )
        
    except Exception as e:
        error_msg = "Ошибка при проверке соединения"
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        
        if 'ping_msg' in locals():
            await ping_msg.edit_text(
                f"❌ {error_msg}\n"
                f"⚠️ Причина: {str(e)}",
                parse_mode="HTML"
            )
        else:
            await message.reply(f"❌ {error_msg}")

@router.message(Command("top"))
@allowed_chat_only()
async def show_top_users(message: Message):
    await log_command(message)
    """
    Показывает топ самых активных пользователей чата.
    """
    try:
        logger.info(f"Команда /top вызвана пользователем {message.from_user.id}")
        
        async with AsyncSessionLocal() as session:
            query = (
                select(UserStats)
                .where(UserStats.chat_id == message.chat.id)
                .order_by(UserStats.message_count.desc())
                .limit(10)
            )
            result = await session.execute(query)
            top_users = result.scalars().all()
            
            if not top_users:
                await message.reply("📊 Статистика сообщений пока не собрана.")
                return
            
            # Формируем сообщение с топом
            top_text = ["<b>📊 Топ 10 активных участников:</b>\n"]
            
            for i, user_stat in enumerate(top_users, 1):
                try:
                    member = await message.chat.get_member(user_stat.user_id)
                    user = member.user
                    username = user.username if user.username else user.full_name
                    
                    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "•")
                    msg_count = format_number(user_stat.message_count)
                    
                    top_text.append(
                        f"{medal} {i}. <a href='tg://user?id={user.id}'>{username}</a>"
                        f"\n└ Сообщений: <code>{msg_count}</code>"
                    )
                    
                except Exception as e:
                    logger.error(f"Ошибка при получении информации о пользователе {user_stat.user_id}: {e}")
                    continue
            
            await message.reply(
                "\n".join(top_text),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            logger.info(f"Топ пользователей успешно отправлен в чат {message.chat.id}")
            
    except Exception as e:
        error_msg = "Произошла ошибка при получении топа пользователей"
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        await message.reply(f"{error_msg}. Пожалуйста, попробуйте позже.")

def format_number(num: int) -> str:
    """Форматирует число для красивого отображения"""
    if num < 1000:
        return str(num)
    elif num < 1000000:
        return f"{num/1000:.1f}K".rstrip('0').rstrip('.')
    else:
        return f"{num/1000000:.1f}M".rstrip('0').rstrip('.')

@router.message(Command("profile"))
@allowed_chat_only()
async def profile_command(message: Message):
    await log_command(message)
    """
    Показывает информацию о профиле пользователя.
    """
    try:
        logger.info(f"Команда /profile вызвана пользователем {message.from_user.id}")
        
        target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        
        async with AsyncSessionLocal() as session:
            query = select(UserStats).where(
                UserStats.user_id == target_user.id,
                UserStats.chat_id == message.chat.id
            )
            result = await session.execute(query)
            user_stats = result.scalar_one_or_none()
            
            chat_member = await message.chat.get_member(target_user.id)
            
            status_emoji = {
                'creator': '👑 Владелец',
                'administrator': '⭐️ Администратор',
                'member': '👤 Участник',
                'restricted': '⚠️ Ограничен',
                'left': '🚶‍♂️ Покинул чат',
                'banned': '🚫 Заблокирован'
            }.get(chat_member.status, '❓ Неизвестно')
            
            profile_text = [
                "<b>👤 Профиль пользователя:</b>",
                f"• Имя: {html.escape(target_user.full_name)}",
                f"• ID: <code>{target_user.id}</code>",
                f"• Статус: {status_emoji}",
                f"• Юзернейм: {f'@{target_user.username}' if target_user.username else 'отсутствует'}"
            ]
            
            if user_stats:
                messages = format_number(user_stats.message_count)
                profile_text.extend([
                    "",
                    "<b>Статистика в чате:</b>",
                    f"• Сообщений: <code>{messages}</code>"
                ])
            else:
                profile_text.append("\n<b>Статистика:</b> данные отсутствуют")
            
            await message.reply(
                "\n".join(profile_text),
                parse_mode='HTML'
            )
            
            logger.info(f"Профиль успешно отправлен для пользователя {target_user.id}")
            
    except Exception as e:
        error_msg = "Произошла ошибка при получении информации о профиле"
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        await message.reply(f"{error_msg}. Пожалуйста, попробуйте позже.")