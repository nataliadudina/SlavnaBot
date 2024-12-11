import logging
from logging.config import dictConfig
import requests

from config import load_bot_config

config = load_bot_config('.env')
super_admin = config.super_admin
bot_token = config.token


class TelegramLogsHandler(logging.Handler):
    """ Класса хендлера для натройки отправки логов в телеграм. """

    def __init__(self, token: str, chat_id: int):
        super().__init__()
        self.bot_token = token
        self.chat_id = chat_id

    def emit(self, record: logging.LogRecord):
        """ Формирование сообщения об ошибки для отправки."""

        try:
            log_entry = self.format(record)  # Форматируем сообщение
            self.send_to_telegram(log_entry)
        except Exception as e:
            print(f"Ошибка в логировании Telegram: {e}")

    def send_to_telegram(self, message: str):
        """ Отправка логов в чат телеграма. """

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {"chat_id": self.chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            # Если произошла ошибка при отправке в Telegram, вывести в консоль
            print(f"Failed to send log to Telegram: {e}")


# Конфигурация логирования
LOGGING_CONFIG = {
    "version": 1,  # Версия конфигурации
    "disable_existing_loggers": False,  # Оставить уже существующие логгеры
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%d-%m-%Y %H:%M",
        },
        "error": {
            "format": "%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d: %(message)s",
            "datefmt": "%d-%m-%Y %H:%M",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        },
    },
    "loggers": {
        "": {  # Корневой логгер для всех уровней
            "level": "INFO",
            "handlers": ["console"],
        },
    },
}


def setup_logging():
    dictConfig(LOGGING_CONFIG)

    # Создаем кастомный обработчик TelegramLogsHandler
    telegram_handler = TelegramLogsHandler(config.token, config.super_admin)
    telegram_handler.setLevel(logging.ERROR)  # Обработчик срабатывает только для ERROR
    telegram_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d: %(message)s'))

    # Получаем корневой логгер
    logger = logging.getLogger()
    logger.addHandler(telegram_handler)
