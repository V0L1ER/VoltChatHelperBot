from utils.logger import BotLogger
from aiogram import Router, Bot, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command
from config import get_settings
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio


# Настройка логирования и конфигурации
logger = BotLogger.get_logger()
settings = get_settings()

router = Router()

class AboutEditStates(StatesGroup):
    waiting_for_about = State()


@router.my_chat_member()
async def handle_bot_status_update(update: ChatMemberUpdated, bot: Bot) -> None:
    """
    Обработчик изменений статуса бота в чате.
    Логирует изменения и выполняет необходимые действия.
    """
    try:
        logger.info(
            f"Bot status updated in chat {update.chat.id}. "
            f"New status: {update.new_chat_member.status}"
        )

        if update.new_chat_member.status == "left":
            logger.warning(f"Бот был удален из чата {update.chat.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изменения статуса бота: {e}", exc_info=True)

@router.chat_member()
async def handle_user_update(update: ChatMemberUpdated, bot: Bot) -> None:
    """
    Обработчик для приветствия новых участников чата.
    """
    try:
        # Проверяем, что это новый участник
        if update.old_chat_member.status != update.new_chat_member.status:
            if update.new_chat_member.status == "member":
                user = update.new_chat_member.user
                welcome_text = (
                    f"👋 Добро пожаловать, {user.mention_html()}!\n"
                    f"Рады видеть вас в нашем чате.\n"
                    f"Пожалуйста, ознакомьтесь с правилами чата, использовав команду <b>/rules</b>."
                )
                
                await bot.send_message(
                    chat_id=update.chat.id,
                    text=welcome_text,
                    parse_mode="HTML"
                )
                logger.info(f"Новый участник {user.id} присоединился к чату {update.chat.id}")
                
    except Exception as e:
        logger.error(f"Ошибка при приветствии нового участника: {e}", exc_info=True)
        
@router.message(Command("edit_about"))
async def edit_about_command(message: Message, state: FSMContext):
    """Команда для изменения информации о боте"""
    if message.chat.type != "private" or message.from_user.id != settings.OWNER_ID:
        return

    await message.answer(
        "Пожалуйста, отправьте новый текст для команды /about.\n"
        "Поддерживается HTML-форматирование.\n"
        "Для отмены используйте /cancel"
    )
    await state.set_state(AboutEditStates.waiting_for_about)

@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    if message.chat.type != "private" or message.from_user.id != settings.OWNER_ID:
        return

    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("Операция отменена.")

@router.message(AboutEditStates.waiting_for_about)
async def process_about_text(message: Message, state: FSMContext):
    """Обработка нового текста для about"""
    if message.chat.type != "private" or message.from_user.id != settings.OWNER_ID:
        return

    if not message.text:
        await message.answer("Пожалуйста, отправьте текстовое сообщение.")
        return

    try:
        # Здесь можно добавить сохранение текста в базу данных или файл
        # Для примера сохраним в файл
        with open('data/about_text.txt', 'w', encoding='utf-8') as f:
            f.write(message.text)

        await message.answer("✅ Информация о боте успешно обновлена!")
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при сохранении информации о боте: {e}")
        await message.answer("❌ Произошла ошибка при сохранении информации.")
        await state.clear()

@router.message(Command("view_about"))
async def view_about_command(message: Message):
    """Просмотр текущей информации о боте"""
    if message.chat.type != "private" or message.from_user.id != settings.OWNER_ID:
        return

    try:
        # Чтение текущего текста
        try:
            with open('data/about_text.txt', 'r', encoding='utf-8') as f:
                about_text = f.read()
        except FileNotFoundError:
            about_text = "Информация о боте ещё не настроена."

        await message.answer(
            "Текущая информация о боте:\n\n"
            f"{about_text}"
        )

    except Exception as e:
        logger.error(f"Ошибка при чтении информации о боте: {e}")
        await message.answer("❌ Произошла ошибка при чтении информации.")
        
@router.message()
async def handle_messages(message: Message) -> None:
    """
    Обработчик всех входящих сообщений.
    """
    try:
        # Игнорируем сообщения от ботов
        if message.from_user and message.from_user.is_bot:
            return

        message_text = message.text[:50] + "..." if message.text else "<Нет текста>"
        logger.info(f"Message from {message.from_user.id if message.from_user else 'Unknown'} "
                   f"in chat {message.chat.id}: {message_text}")

        if message.chat.type == "private":
            if message.from_user.id == settings.OWNER_ID:
                await message.answer(
                    f"👋 Добро пожаловать в админ-панель, {message.from_user.full_name}!\n\n"
                    "Доступные команды:\n"
                    "/edit_about - Изменить информацию о боте\n"
                    "/view_about - Посмотреть текущую информацию"
                )
                return
            await message.answer("Извините, бот не доступен для личных чатов.")
            return

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
        try:
            await message.bot.send_message(
                chat_id=settings.SHARECHAT_ID,
                text=f"❗️ Ошибка при обработке сообщения:\n{str(e)}"
            )
        except Exception as api_error:
            logger.error(f"Не удалось отправить уведомление об ошибке: {api_error}")
            

@router.channel_post()
async def handle_channel_post(message: Message):
    channel_id = settings.CHANNEL_ID
    message_id = message.message_id
    logger.info(f"Получено новое сообщение в канале {channel_id}: {message_id}")

    try:
        # Сначала ждем подольше, чтобы сообщение точно успело закрепиться
        await asyncio.sleep(10)
        
        # Максимальное количество попыток
        max_attempts = 12  # Увеличили количество попыток
        attempt = 0
        
        while attempt < max_attempts:
            # Получаем информацию о чате и закрепленном сообщении
            chat = await message.bot.get_chat(settings.CHAT_ID)
            
            if not chat.pinned_message:
                logger.error("Закрепленное сообщение не найдено")
                await asyncio.sleep(5)
                attempt += 1
                continue
            
            pinned = chat.pinned_message
            
            # Проверяем, что это нужное сообщение из канала
            if (pinned.forward_from_chat and 
                pinned.forward_from_chat.id == channel_id and 
                pinned.forward_from_message_id == message_id):
                
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Правила", callback_data='chat_rules')]
                ])
                
                await message.bot.send_message(
                    chat_id=settings.CHAT_ID,
                    text=(
                        "⬇️ Прежде чем писать, ознакомься с правилами! ⬇️"
                    ),
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_to_message_id=pinned.message_id,
                    reply_markup=keyboard
                )
                logger.info(f"✅ Комментарий отправлен к закрепленному сообщению в супергруппе")
                return
            else:
                logger.info(f"Попытка {attempt}: Ждем нужное сообщение (текущее: {pinned.forward_from_message_id}, ожидаем: {message_id})")
            
            await asyncio.sleep(5)
            attempt += 1
        
        logger.error("Превышено максимальное количество попыток")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при отправке комментария: {str(e)}"
        logger.error(error_msg)
            
            
@router.callback_query(F.data == 'chat_rules')
async def chat_rules(callback: CallbackQuery):
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
    await callback.message.reply(rules_text, parse_mode="Markdown")
    await callback.answer()
