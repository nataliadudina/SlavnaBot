import logging
from datetime import datetime, date, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

import bot.keyboards.keyboards as kb
from bot.filters.filters import IsAdminOrGuide, is_admin, is_guide
from bot.handlers.period_handlers import DatesInputState
from bot.keyboards.calendar import generate_calendar
from bot.keyboards.pagination_kb import create_pagination_keyboard
from bot.texts.staff_texts import buttons, replies
from googlesheets.tours_filtering import filter_by_date, filter_by_guide_on_date

router = Router()
router.message.filter(IsAdminOrGuide())

logger = logging.getLogger(__name__)


# Состояние для ожидания даты
class DateInputState(StatesGroup):
    due_date = State()


# Создание inline клавиатур при нажатии reply button
@router.message(F.text == buttons['on_date'])
async def make_date_keyboard(message: Message):
    """
    Обработка кнопки 'Экскурсии на дату'.
    При нажатии кнопки создаются inline buttons с выбором.
    """
    await message.answer(text='Что показать?',
                         reply_markup=kb.date_keyboard)


# Эти хэндлеры будет срабатывать на апдейты типа CallbackQuery
# при нажатии inline кнопок
@router.callback_query(F.data == 'date_pressed')
async def handle_date_tours(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие inline кнопки 'Экскурсии на дату'.
    Отправляет пользователю сообщения с inline календарём.
    """
    today = datetime.today()
    keyboard = await generate_calendar(today.year, today.month)
    await callback.message.edit_text(text='На какую дату найти экскурсии?',
                                     reply_markup=keyboard)
    await callback.answer()
    await state.set_state(DateInputState.due_date)


@router.callback_query(lambda c: c.data.startswith("navigate_"))
async def navigate_calendar(callback_query: CallbackQuery):
    """ Навигация по календарю: вперёд, назад. """
    _, year, month = callback_query.data.split("_")
    keyboard = await generate_calendar(int(year), int(month))
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()


@router.callback_query((F.data.startswith('date_') | F.data.in_(['today_pressed', 'tomorrow_pressed'])))
async def handle_near_tours(callback: CallbackQuery, state: FSMContext):
    """
    Обработка выбора даты: сегодня, завтра, или конкретная дата.
    Запускает функцию поиска экскурсий из googlesheet, запланированных на выбранную дату.
    """
    await callback.answer(f"Ищу экскурсии 🔎")

    # Определяем дату в зависимости от callback.data
    if callback.data == 'today_pressed':
        orders_date = date.today()
    elif callback.data == 'tomorrow_pressed':
        orders_date = date.today() + timedelta(days=1)
    elif callback.data.startswith('date_'):
        # Извлечение выбранной даты из inline календаря
        selected_date = callback.data.split('_')[1]
        orders_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        await state.update_data(due_date=str(orders_date))
        # Показ выбранной даты
        selected_date = datetime.strftime(orders_date, '%d.%m.%Y')
        await callback.answer(selected_date)
    else:
        await callback.answer("Неизвестная команда.")
        return

    # Сброс состояния, если выбор завершён
    await state.clear()

    # Получаем user_id из callback
    user_id = callback.from_user.id

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
