import logging
import sys
from datetime import datetime
from logging.config import dictConfig
from zoneinfo import ZoneInfo

import requests

from .config import config

super_admin = config.super_admin
bot_token = config.token


TZ = ZoneInfo("Europe/Moscow")


class LocalTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=TZ)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(sep=' ', timespec='seconds')


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
            # Report failures without triggering logging recursion.
            self.handleError(record)

    def send_to_telegram(self, message: str):
        """ Send a formatted log message to Telegram. """

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}
        try:
            response = requests.post(url, data=payload, timeout=5)
            if not response.ok:
                sys.stderr.write(f'Telegram API error: {response.status_code} {response.text}\n')
        except Exception as e:
            sys.stderr.write(f'Telegram logging failed: {e}\n')  # feedback without recursion


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "()": "src.logging_config.LocalTimeFormatter",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%d-%m-%Y %H:%M",
        },
        "telegram": {
            "()": "src.logging_config.LocalTimeFormatter",
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
        'telegram': {
            '()': 'src.logging_config.TelegramLogsHandler',
            'level': 'ERROR',
            'formatter': 'telegram',
            'token': bot_token,
            'chat_id': super_admin

        }
    },
    "root": {  # fallback configuration
        "level": "INFO",
        "handlers": ["console", "telegram"],
    },
}


def setup_logging():
    """Configure application logging."""
    dictConfig(LOGGING_CONFIG)
