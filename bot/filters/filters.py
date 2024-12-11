from aiogram.filters import BaseFilter
from aiogram.types import Message

from config import bot_config


def is_admin(user_id):
    """ Проверяет, является ли пользователь админом."""
    return user_id in bot_config.admin_ids


def is_guide(user_id):
    """ Проверяет, является ли пользователь гидом."""
    return user_id in bot_config.guide_ids


class IsAdmin(BaseFilter):
    """Фильтрует пользователей, которые состоят в группе администраторов."""

    def __init__(self):
        self.admin_ids = bot_config.admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


class IsAdminOrGuide(BaseFilter):
    """Фильтрует пользователей, которые состоят в группе администраторов или гидов."""

    def __init__(self):
        self.admin_ids = bot_config.admin_ids
        self.guide_ids = bot_config.guide_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids or message.from_user.id in self.guide_ids
