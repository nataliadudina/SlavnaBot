import logging
from datetime import datetime, date, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

import bot.keyboards as kb
from bot.filters import IsAdminOrGuide, is_admin, is_guide, is_superadmin
from bot.keyboards.calendar import generate_calendar
from bot.keyboards.pagination_kb import create_pagination_keyboard
from bot.texts.staff_texts import buttons, replies, tour_texts
from googlesheets.tours_filtering import filter_by_date, filter_for_sa_date

router = Router()
router.message.filter(IsAdminOrGuide())

logger = logging.getLogger(__name__)


class DateInputState(StatesGroup):
    due_date = State()


# ============= Inline keyboard =============
@router.message(F.text == buttons['on_date'])
async def make_date_keyboard(message: Message):
    """
    Handles the 'Экскурсии на дату' button.
    Creates inline buttons with selection options.
    """
    await message.answer(text='Что показать?',
                         reply_markup=kb.date_keyboard)


# ============= CallbackQueries =============
@router.callback_query(F.data == 'date_pressed')
async def handle_date_tours(callback: CallbackQuery, state: FSMContext):
    """
    Handles the 'Выбрать дату' inline button.
    Sends the user messages with an inline calendar.
    """
    today = datetime.today()
    calendar = await generate_calendar(today.year, today.month)
    await callback.message.edit_text(text=f"На какую дату найти экскурсии?\n\n"
                                          f"{tour_texts['cancel_search']}",
                                     reply_markup=calendar)
    await callback.answer()
    await state.set_state(DateInputState.due_date)


@router.callback_query(lambda c: c.data.startswith("navigate_"))
async def navigate_calendar(callback_query: CallbackQuery):
    """ Calendar navigation: forward, backward. """
    try:
        _, year, month = callback_query.data.split("_")
        calendar = await generate_calendar(int(year), int(month), is_period=False)
        await callback_query.message.edit_reply_markup(reply_markup=calendar)
        await callback_query.answer()
    except ValueError:
        await callback_query.answer("Некорректные данные навигации.")


@router.callback_query((F.data.startswith('date_') | F.data.in_(['today_pressed', 'tomorrow_pressed', 'check'])))
async def handle_near_tours(callback: CallbackQuery, state: FSMContext):
    """
    Handles date selection: today, tomorrow, or a specific date.
    Triggers searching for tours from Google Sheets scheduled for the selected date.
    """
    await callback.answer(f"Ищу экскурсии 🔎")

    if callback.data == 'today_pressed':
        orders_date = date.today()
    elif callback.data in ('tomorrow_pressed', 'check'):
        orders_date = date.today() + timedelta(days=1)
    elif callback.data.startswith('date_'):
        # A date from inline calendar
        selected_date = callback.data.split('_')[1]
        orders_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        await state.update_data(due_date=str(orders_date))
    else:
        await callback.answer("Неизвестная команда.")
        return

    await state.clear()

    user_id = callback.from_user.id

    if orders_date < date.today():
        await callback.message.answer(f"Информация на {orders_date.strftime('%d.%m.%Y')} недоступна. "
                                      "Возможен поиск только предстоящих экскурсий. 😈")
    else:
        try:
            # Search for tours from Google Sheets for admins
            if is_superadmin(user_id):
                tours, errors = filter_for_sa_date(orders_date)
            elif is_admin(user_id):
                tours, errors = filter_by_date(orders_date)
            # Search for tours from Google Sheets for guides
            elif is_guide(user_id):
                tours, errors = filter_by_date(orders_date, guide=user_id)
            else:
                await callback.answer("У вас нет прав для выполнения этой команды.")
                return
        except Exception as e:
            logger.error(f"Error during tour filtering for user {user_id}: {e}")
            await callback.message.answer("Произошла ошибка при обработке вашего запроса. Попробуйте позже.")
            return

        if not tours and not errors:
            await callback.message.answer(replies['no_excursions'])
            return

        await state.update_data(tours=tours)

        if tours:
            current_page = 1
            total_pages = len(tours)
            tour = tours[current_page - 1]
            tour_info = "\n".join(f"<b>{header}</b>: {info}" for header, info in tour.items())

            await callback.message.answer(
                text=tour_info,
                reply_markup=create_pagination_keyboard(current_page, total_pages)
            )

        if errors:
            errors_list = '\n'.join(errors)
            await callback.message.answer(
                f"⚠️ Найдены ошибки в записи для экскурсий:\n"
                f"{errors_list}.\n<b>Сообщите, пожалуйста, администратору</b>."
            )


@router.callback_query(F.data.startswith('page:'))
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    """ Handles pagination callbacks for navigating through tour listings. """
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


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer("Эта кнопка неактивна.", show_alert=False)
