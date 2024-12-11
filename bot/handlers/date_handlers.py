import logging
from datetime import date, timedelta

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery

from bot.filters.filters import is_admin, is_guide, IsAdminOrGuide
import bot.keyboards.keyboards as kb
from bot.keyboards.pagination_kb import create_pagination_keyboard
from bot.texts.staff_texts import replies, buttons
from googlesheets.tours_filtering import filter_by_date, filter_by_guide_on_date

router = Router()
router.message.filter(IsAdminOrGuide())

logger = logging.getLogger(__name__)


# Создание inline клавиатур при нажатии reply button
@router.message(F.text == buttons['on_date'])
async def make_date_keyboard(message: Message):
    """ При нажатии кнопки 'Экскурсии на дату' создаются inline buttons с выбором даты. """
    await message.answer(text='Что показать?',
                         reply_markup=kb.date_keyboard)


# Эти хэндлеры будет срабатывать на апдейты типа CallbackQuery
# при нажатии inline кнопок

@router.callback_query(F.data.in_(['today_pressed', 'tomorrow_pressed']))
async def handle_near_tours(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает запрос экскурсий на сегодня и завтра.
    Отправляет информацию об экскурсиях, запланированных на текущий день или завтра.
    """
    await callback.answer(f"Ищу экскурсии 🔎")

    # Получаем user_id из callback
    user_id = callback.from_user.id

    # Определяем дату в зависимости от callback.data
    if callback.data == 'today_pressed':
        orders_date = date.today()
    elif callback.data == 'tomorrow_pressed':
        orders_date = date.today() + timedelta(days=1)
    else:
        await callback.answer("Неизвестная команда.")
        return
    try:
        # Поиск экскурсий из гугл докса для админов
        if is_admin(user_id):
            tours = filter_by_date(orders_date)
        # Поиск экскурсий из гугл докса для гидов
        elif is_guide(user_id):
            tours = filter_by_guide_on_date(user_id, orders_date)
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

    # Сохраняем информацию об экскурсиях для использования в списке с пагинацией
    await state.update_data(tours=tours)

    # Формируем первую страницу
    current_page = 1
    total_pages = len(tours)
    tour = tours[current_page - 1]  # Индексация с 0
    tour_info = "\n".join(f"<b>{header}</b>: {info}" for header, info in tour.items())

    await callback.message.edit_text(
        text=tour_info,
        reply_markup=create_pagination_keyboard(current_page, total_pages)
    )


@router.callback_query(F.data == 'date_pressed')
async def handle_date_tours(callback: CallbackQuery):
    """
    Обрабатывает запрос экскурсий на дату.
    Отправляет информацию об экскурсиях, запланированных на конкретную дату.
    """
    await callback.answer(f"Ищу экскурсии 🔎")
    # дописать поиск по дате


@router.callback_query(F.data.startswith('page:'))
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    current_page = int(callback.data.split(":")[1])
    user_data = await state.get_data()
    tours = user_data.get("tours", [])

    if not tours or current_page < 1 or current_page > len(tours):
        await callback.answer("Ошибка: Неверный номер страницы.")
        return

    tour = tours[current_page - 1]
    tour_info = "\n".join(f"<b>{header}</b>: {info}" for header, info in tour.items())
    total_pages = len(tours)

    await callback.message.edit_text(
        text=tour_info,
        reply_markup=create_pagination_keyboard(current_page, total_pages)
    )


# Этот хэндлер срабатывает на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключает машину состояний
@router.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(
        text=''
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()
