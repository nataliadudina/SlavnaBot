import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

import bot.keyboards.keyboards as kb
from bot.filters.filters import is_admin, is_guide
from bot.texts.staff_texts import replies, buttons
from googlesheets.tours_filtering import filter_by_period, filter_by_guide_on_period

router = Router()

logger = logging.getLogger(__name__)


@router.message(F.text == buttons['on_period'])
async def make_period_keyboard(message: Message):
    """ При нажатии кнопки 'Экскурсии на период' создаются inline buttons с дальнейшим выбором. """
    await message.answer(text='Что смотрим?',
                         reply_markup=kb.period_keyboard)


@router.callback_query(F.data == 'all_tours_pressed')
async def handle_all_tours(callback: CallbackQuery):
    """
    Обрабатывает запрос всех экскурсий.
    Отправляет информацию обо всех запланированных экскурсиях.
    """

    await callback.answer(f"Загружаю список экскурсии 📝")

    # Получаем user_id из callback
    user_id = callback.from_user.id

    try:
        # Поиск экскурсий из гугл докса для админа
        if is_admin(user_id):
            tours = filter_by_period()
        # Поиск экскурсий из гугл докса для гидов
        elif is_guide(user_id):
            tours = filter_by_guide_on_period(user_id)
        else:
            await callback.answer("У вас нет прав для выполнения этой команды.")
            return
    except Exception as e:
        logger.error(f"Ошибка при фильтрации экскурсий у {user_id}: {e}")
        await callback.message.answer("Произошла ошибка при обработке вашего запроса. Попробуйте позже.")
        return

    if not tours:
        await callback.message.answer(replies['no_excursions'])
        return

    # Отправляем информацию об экскурсиях
    for row in tours:
        tour_info = "\n".join(f"<b>{header}</b>: {info}" for header, info in row.items())
        await callback.message.answer(tour_info)


@router.callback_query(F.data == 'period_pressed')
async def handle_period_tours(callback: CallbackQuery):
    """
   Обрабатывает запрос экскурсий за период.
   Отправляет информацию обо всех экскурсиях за определённый период.
   """
    await callback.answer(f"Загружаю список экскурсии.")
    # дописать поиск по датам
