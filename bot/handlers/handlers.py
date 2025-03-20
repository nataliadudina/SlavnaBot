import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter, or_f
from aiogram.fsm.state import default_state
from aiogram.types import Message

import bot.keyboards.keyboards as kb
from bot.db.db import add_to_db, update_user_role
from bot.filters.filters import is_admin, is_guide
from bot.texts.other_texts import gen_answer, cmd_texts
from bot.texts.staff_texts import replies

router = Router()

logger = logging.getLogger(__name__)


@router.message(CommandStart(), StateFilter(default_state))
async def cmd_start(message: Message):
    """ При запуске бота создаётся клавиатура с reply buttons. """
    user_id = message.from_user.id
    name = message.from_user.first_name or message.from_user.username
    username = message.from_user.username or 'Unknown'

    # Добавляем пользователя в базу данных (если его там нет)
    await add_to_db(user_id, username)

    # Создание reply клавиатуры для админа
    if is_admin(user_id):
        await update_user_role(user_id, "admin")
        await message.answer(
            text=f"Привет, {name}! 🌞",

            reply_markup=kb.admin_keyboard,
            input_field_placeholder="Нажмите кнопку"
        )
    # Создание reply клавиатуры для гида
    elif is_guide(user_id):
        await update_user_role(user_id, "guide")
        await message.answer(
            f"Привет, {name}! 🪻",
            reply_markup=kb.guide_keyboard,
            input_field_placeholder="Нажмите кнопку"
        )
    # Создание reply стандартной клавиатуры
    else:
        await message.answer(
            text=replies['greeting'],
            reply_markup=kb.user_keyboard
        )
    logging.info(f'{message.from_user.id} connected.')


@router.message(Command('kb'))
async def cmd_keyboard(message: Message):
    """Отправляет reply клавиатуру по запросу команды /kb."""
    user_id = message.from_user.id

    # Определяем клавиатуру по роли пользователя
    keyboard = get_keyboard_for_user(user_id)

    await message.answer(
        text='Вжух 🪄',
        reply_markup=keyboard
    )


def get_keyboard_for_user(user_id):
    """Определяет, какую клавиатуру отправить пользователю."""
    if is_admin(user_id):
        return kb.admin_keyboard
    elif is_guide(user_id):
        return kb.guide_keyboard
    return kb.user_keyboard


# Ответ при запросе экскурсий
@router.message(F.text == 'Экскурсии 🗺️')
async def handle_tours(message: Message):
    await message.answer('Вот варианты экскурсий')


# Ответ при запросе контактов
@router.message(or_f(F.text == 'Контакты 📩', Command(commands='contacts')), StateFilter(default_state))
async def cmd_contacts(message: Message):
    await message.answer(cmd_texts['contacts'])


@router.message(Command(commands='help'), StateFilter(default_state))
async def cmd_help(message: Message):
    await message.answer(cmd_texts['help'])


@router.message(Command(commands='info'), StateFilter(default_state))
async def cmd_info(message: Message):
    await message.answer(cmd_texts['info'])


@router.message(Command(commands='slavna'), StateFilter(default_state))
async def cmd_slavna(message: Message):
    await message.answer(cmd_texts['slavna'])


@router.message(StateFilter(default_state))
async def cmd_gen(message: Message, ):
    await message.answer(gen_answer)
