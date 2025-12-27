from aiogram.filters import BaseFilter
from aiogram.types import Message

from config import config


def is_superadmin(user_id):
    """ Checks whether the user is a super admin. """
    return user_id == config.super_admin


def is_admin(user_id):
    """ Checks whether the user is an admin. """
    return user_id in config.admin_ids


def is_guide(user_id):
    """ Checks whether the user is a guide. """
    return user_id in config.guide_ids


class IsAdmin(BaseFilter):
    """ Filters users who belong to the administrators group. """

    def __init__(self):
        self.admin_ids = config.admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


class IsAdminOrGuide(BaseFilter):
    """ Filters users who belong to either the administrators or guides groups. """

    def __init__(self):
        self.admin_ids = config.admin_ids
        self.guide_ids = config.guide_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids or message.from_user.id in self.guide_ids
