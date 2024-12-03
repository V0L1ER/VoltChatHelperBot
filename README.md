﻿# **Telegram Bot для Модерации Группового Чата**

## **Описание**

Этот бот предназначен для модерации и управления групповыми чатами в Telegram. Он предоставляет широкий спектр функций, таких как выдача предупреждений, управление правами участников, интеграция с YouTube для уведомления о новых видео, и многое другое. Бот разработан с использованием библиотеки **aiogram 3.x** и поддерживает асинхронные операции для высокой производительности.

### **Функциональность**

- **Модерация чата:**
  - Выдача предупреждений пользователям.
  - Автоматическое удаление сообщений с нежелательным контентом.
  - Временный или постоянный мут и бан пользователей.
- **Уведомления о новых видео:**
  - Отслеживание определённого YouTube-канала.
  - Автоматическая отправка сообщений в канал при выходе нового видео.
- **Интерактивные команды:**
  - Создание опросов и викторин.
  - Установка напоминаний.
  - Приветствие новых участников.
- **Статистика:**
  - Отслеживание активности пользователей.
  - Команда для отображения статистики чата.

## **Установка**

### **Требования**

- Python 3.7 или выше
- Созданный бот в Telegram с полученным токеном
- YouTube Data API ключ

### **Шаги установки**

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/V0L1ER/VoltChatHelperBot.git
   cd VoltChatHelperBot
   ```

2. **Создайте виртуальное окружение и активируйте его:**

   ```bash
   python -m venv venv
   # Для Windows
   venv\Scripts\activate
   # Для Linux/MacOS
   source venv/bin/activate
   ```

3. **Установите зависимости:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Настройте переменные окружения:**

   Создайте файл `.env` и добавьте в него следующие переменные:

   ```env
   BOT_TOKEN = ваш_токен_бота
   CHAT_ID=ID_вашего_чата_для_осуждений
   CHANNEL_ID=ID_вашего_канала
   ADMIN_IDS= ID_ваших_администраторов
   SHARECHAT_ID=ID_вашего_чата_для_репортов
   YOUTUBE_API_KEY=ваш_YouTube_API_ключ
   YOUTUBE_CHANNEL_ID=ID_YouTube_канала
   ```

5. **Запустите бота:**

   ```bash
   python bot.py
   ```

## **Использование**

### **Основные команды**

- `/help` — Отображает список доступных команд.
- `/warn` — Выдаёт предупреждение пользователю (использовать в ответ на сообщение).
- `/listwarns` — Показывает список предупреждений с указанием юзернеймов.
- `/remwarns` — Сбрасывает предупреждения пользователя (использовать в ответ на сообщение).
- `/mute` — Замутить пользователя на определённое время.
- `/unmute` — Снять мут с пользователя.
- `/ban` — Заблокировать пользователя.
- `/unban` — Разблокировать пользователя.
- `/kick` — Исключить пользователя из чата.
- `/stats` — Показать статистику активности в чате.
- `/poll` — Создать опрос (например: `/poll Ваш вопрос | Вариант 1 | Вариант 2`).

### **Пример использования команды `/poll`**

Создание анонимного опроса:

```bash
/poll Какой ваш любимый язык программирования? | Python | JavaScript | C++ | Java
```

## **Функции модерации**

- **Выдача предупреждений:** Администраторы могут выдавать предупреждения пользователям за нарушение правил. При достижении определённого количества предупреждений могут применяться санкции (мут, бан).
- **Управление правами:** Возможность мутить, банить, кикать и разбанивать пользователей.
- **Автоматическая модерация:** Бот может автоматически удалять сообщения с нежелательным контентом, таким как спам или нецензурная лексика.

## **Интеграция с YouTube**

Бот отслеживает указанный YouTube-канал и отправляет уведомления в чат при выходе новых видео. Это реализовано с использованием YouTube Data API и асинхронных запросов.

## **Статистика чата**

Команда `/stats` отображает самые активные пользователи в чате, основываясь на количестве отправленных сообщений.

## **Настройка и кастомизация**

- **Переменные окружения:** Используются для хранения конфиденциальной информации и настроек бота.
- **Файлы конфигурации:** Вы можете настроить различные параметры бота, изменяя файлы конфигурации или переменные окружения.
- **Расширяемость:** Код бота написан с возможностью лёгкого добавления новых функций и команд.

## **Вклад в проект**

Если вы хотите внести свой вклад в развитие бота:

1. Форкните репозиторий.
2. Создайте новую ветку для своей функции (`git checkout -b feature/NewFeature`).
3. Сделайте коммит своих изменений (`git commit -am 'Добавлена новая функция'`).
4. Запушьте ветку (`git push origin feature/NewFeature`).
5. Создайте Pull Request.

## **Лицензия**

Этот проект лицензируется под лицензией MIT — подробности см. в файле [LICENSE](LICENSE).

## **Связаться с нами**

- **Telegram:** [@v0l1er](https://t.me/v0l1er)
- **Email:** nikityukvova18@gmail.com

---

Если у вас есть дополнительные вопросы или вам нужна помощь с настройкой или использованием бота, пожалуйста, не стесняйтесь обращаться.
