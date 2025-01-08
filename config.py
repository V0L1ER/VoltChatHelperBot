from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import json

class Settings(BaseSettings):
    # Основные настройки бота
    BOT_TOKEN: str
    CHAT_ID: int
    CHANNEL_ID: int
    SHARECHAT_ID: int
    
    # Настройки базы данных
    DATABASE_URL: str
    
    # Настройки модерации
    WARN_LIMIT: int = 3
    FORBIDDEN_WORDS: List[str] = [
        "хохол", 
        "гитлер", 
        "сталин",
        "нацист", "фашист", "националист",
        "ХОХОЛ", "Хохол", "хОхОл",
        "путлер", "пу", "диктатор",
        "террорист", "экстремист",
        
        # Азартные игры и казино
        "1win", "1 win", "1вин", "1 вин",
        "onewin", "one win", "ванвин", "ван вин",
        "казино", "casino", "cazino",
        "ставки", "букмекер", "бк",
        "1xbet", "1хбет", "1 x bet",
        "melbet", "мелбет", "mel bet",
        "бетсити", "фонбет", "лига ставок",
        "париматч", "parimatch", "pari match",
        "азино", "azino", "777",
        "вулкан", "vulkan", "vulcan",
        "джойказино", "joycasino", "joy casino",
        "покер", "poker", "рулетка",
        "слоты", "автоматы", "игровые автоматы",
        "betting", "bet", "беттинг",
        "промокод", "promo", "бонус",
        "зеркало казино", "доступ к казино",
        "вывод денег", "заработок", "обыграть казино",
        
        # Новые запрещенные слова и их вариации
        "cock", "cunt", "fuck", "fucker", "fucking",
        "zaeb", "zaebal", "zaebali", "zaebat",
        "вафел", "вафлёр", "гавно", "гавнюк", "гамно",
        "гандон", "гнид", "гнида", "гниды",
        "говно", "говнюк", "говняк",
        "дрист", "дристать", "дрочить",
        "елда", "елдак", "залуп", "залупа",
        "конча", "курва", "лох", "лошара",
        "манда", "мразь", "мудак", "мудила",
        "нахер", "нахуй", "нехера", "нихера",
        "педик", "педрик", "педрила",
        "писька", "писюн", "потаскуха",
        "херня", "херовый", "хрен",
        "чмо", "чмошник", "чмырь",
        "шалава", "шлюха", "шлюшка"
    ]
    
    # Настройки администрирования
    ADMIN_IDS: str = ""  # Теперь это строка
    
    # Дополнительные настройки
    MESSAGE_DELETION_DELAY: int = 5  # секунды
    MAX_WARNINGS_HISTORY: int = 100  # количество предупреждений для хранения
    
    # Добавляем в класс Settings
    SPAM_TIME_WINDOW: int = 10  # секунды
    SPAM_MESSAGE_LIMIT: int = 5  # сообщений
    SPAM_WARN_DELETION_DELAY: int = 5  # секунды
    
    # Добавить новые настройки в класс Settings:
    OWNER_ID: int
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def admin_ids_list(self) -> List[int]:
        """Преобразует строку с ID админов в список целых чисел"""
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(',')]

@lru_cache()
def get_settings() -> Settings:
    """
    Получение настроек с кэшированием
    """
    return Settings() 