import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

class BotLogger:
    _instance: Optional[logging.Logger] = None

    @staticmethod
    def setup() -> logging.Logger:
        if BotLogger._instance is not None:
            return BotLogger._instance

        logger = logging.getLogger('telegram_bot')
        logger.setLevel(logging.INFO)

        # Создаем форматтер для логов
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Создаем директорию для логов если её нет
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Настраиваем файловый обработчик
        file_handler = RotatingFileHandler(
            filename=f'{log_dir}/bot.log',
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Добавляем только файловый обработчик к логгеру
        logger.addHandler(file_handler)

        BotLogger._instance = logger
        return logger

    @staticmethod
    def get_logger() -> logging.Logger:
        if BotLogger._instance is None:
            return BotLogger.setup()
        return BotLogger._instance