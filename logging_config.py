import logging
import sys
from logging.config import dictConfig

import requests

from config import config

super_admin = config.super_admin
bot_token = config.token


class TelegramLogsHandler(logging.Handler):
    """ Logging handler that sends error logs to a Telegram chat. """

    def __init__(self, token: str, chat_id: int):
        super().__init__()
        self.bot_token = token
        self.chat_id = chat_id

    def emit(self, record: logging.LogRecord):
        """ Format and send the log record to Telegram. """

        try:
            message = self.format(record)
            self.send_to_telegram(message)
        except Exception:
            # Prevent logging recursion and crashes inside logging system
            self.handleError(record)

    def send_to_telegram(self, message: str):
        """ Send a formatted log message to Telegram. """

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}
        try:
            requests.post(url, data=payload, timeout=5)
        except Exception as e:
            sys.stderr.write(f'Telegram logging failed: {e}\n')  # feedback without recursion


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
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
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}


def setup_logging():
    """Configure application logging."""
    dictConfig(LOGGING_CONFIG)

    # Custom TelegramLogsHandler
    telegram_handler = TelegramLogsHandler(config.token, config.super_admin)
    telegram_handler.setLevel(logging.ERROR)  # for ERROR level only
    telegram_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d: %(message)s'))

    # Get root logger
    logging.getLogger().addHandler(telegram_handler)
