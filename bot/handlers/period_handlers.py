import asyncio
import logging
from datetime import datetime, date
from typing import Optional

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

import bot.keyboards.keyboards as kb
from bot.filters.filters import is_admin, is_guide, is_superadmin
from bot.keyboards.calendar import generate_calendar
from bot.texts.staff_texts import buttons, tour_texts
from googlesheets.tours_filtering import filter_by_period, filter_for_sa_period

router = Router()

logger = logging.getLogger(__name__)


# Состояние для ожидания дат
class DatesInputState(StatesGroup):
    start_date = State()
    end_date = State()


async def send_tours_list(tours: list[dict], errors: list[str], message: Message,
                          start_date: Optional[str] = None, end_date: Optional[str] = None):
    """ Вывод сообщений с найденными экскурсиями или сообщения, что экскурсий нет."""
    if not tours and not errors:
        await message.answer(f"Нет экскурсий с {start_date} по {end_date} 🥺")
        return

    if tours:
        for row in tours:
            tour_info = "\n".join(f"<b>{header}</b>: {info}" for header, info in row.items())
            await message.answer(tour_info)

        if start_date and end_date:
            await message.answer(f"С {start_date} по {end_date} найдено экскурсий: {len(tours) + len(errors)}.")
        else:
            await message.answer(f'Всего экскурсий: {len(tours) + len(errors)}')

    # Отправка предупреждения, если есть ошибки
    if errors:
        errors_list = '\n'.join(errors)
        await message.answer(
            f"⚠️ Найдены ошибки в записи для экскурсий:\n"
            f"{errors_list}.\nСообщите, пожалуйста, администратору."
        )


@router.message(F.text == buttons['on_period'])
async def make_period_keyboard(message: Message):
    """ При нажатии кнопки 'Экскурсии на период' создаются inline buttons с дальнейшим выбором. """
    # Устанавливаем флаг on_period в состояние
    await message.answer(text='Что смотрим?',
                         reply_markup=kb.period_keyboard)


@router.callback_query(F.data == 'period_pressed')
async def handle_period_tours(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие inline кнопки 'Экскурсии на дату'.
    Отправляет пользователю сообщения с inline календарём.
    """
    today = datetime.today()
    keyboard = await generate_calendar(today.year, today.month, is_period=True)
    await callback.message.answer(text=f"Выберите первую дату.\n\n"
                                       f"{tour_texts['cancel_search']}",
                                  reply_markup=keyboard)
    await callback.answer()
    await state.set_state(DatesInputState.start_date)
    await state.update_data(is_period=True)


@router.callback_query(lambda c: c.data.startswith("pnavigate_"))
async def navigate_period_calendar(callback_query: CallbackQuery, state: FSMContext):
    """ Навигация по календарю: вперёд, назад. """
    user_data = await state.get_data()
    logger.info(f"State: {await state.get_state()}, User Data: {user_data}")

    if not user_data.get('is_period', False):
        logger.warning(f"User attempted to navigate calendar outside of period selection. Data: {callback_query.data}")
        await callback_query.answer("Некорректное действие.")
        return

    _, year, month = callback_query.data.split("_")
    year, month = int(year), int(month)

    # Сохраняем текущий год и месяц в состоянии
    await state.update_data(current_year=year, current_month=month)

    # Генерируем календарь
    keyboard = await generate_calendar(year, month, is_period=True)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()


@router.callback_query(F.data.startswith('period_date_'), StateFilter(DatesInputState.start_date))
async def handle_start_date(callback: CallbackQuery, state: FSMContext):
    """ Обработка выбора начальной даты для периода. """
    start_date_str = callback.data.split('_')[2]
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()  # для вывода пользователю
    # Сохраняем начальную дату в состоянии
    await state.update_data(start_date=start_date_str,  current_year=start_date.year, current_month=start_date.month)

    # Показ выбранной даты и запрос конечной
    await callback.answer(f"{start_date.strftime('%d.%m.%Y')}. Выберете вторую дату.")

    # Получаем текущие данные из состояния, чтобы использовать их для подсветки
    user_data = await state.get_data()
    current_year = user_data.get("current_year", datetime.today().year)
    current_month = user_data.get("current_month", datetime.today().month)

    # Генерация календаря с выделением выбранной начальной даты и с учётом раннее выбранного месяца и года
    keyboard = await generate_calendar(current_year, current_month, is_period=True, selected_start_date=start_date_str)
    await callback.message.edit_text(f"Выберите вторую дату.\n\n"
                                     f"{tour_texts['cancel_search']}",
                                     reply_markup=keyboard)
    await state.set_state(DatesInputState.end_date)


@router.callback_query(F.data.startswith('period_date_'), StateFilter(DatesInputState.end_date))
async def handle_end_date(callback: CallbackQuery, state: FSMContext):
    """ Обработка выбора конечной даты для периода. """
    end_date_str = callback.data.split('_')[2]
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Получаем начальную дату из состояния
    user_data = await state.get_data()
    start_date_str = user_data.get("start_date")
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    # Проверка, что начальная дата была выбрана и корректность периода
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    # Сохраняем конечную дату
    await state.update_data(end_date=end_date_str)

    # Форматирование дат для показа
    first_date = start_date.strftime('%d.%m.%Y')
    second_date = end_date.strftime('%d.%m.%Y')
    await callback.answer(f"Ищу заказы с {first_date} по {second_date} 🕝 ...")
    # Удаляем сообщение с текстом и клавиатурой, т.к. второй раз воспользоваться нельзя
    await asyncio.sleep(0.5)
    await callback.message.delete()

    # Удаляем данные о состоянии календаря
    await state.update_data(current_year=None, current_month=None)

    # После выбора обеих дат можно продолжить обработку
    await handle_tours_by_period(callback, state)


@router.callback_query(F.data.startswith('period_date_') & F.state == DatesInputState.end_date)
async def handle_tours_by_period(callback: CallbackQuery, state: FSMContext):
    """ Обработка туров за выбранный период. """
    user_data = await state.get_data()
    start_date_str = user_data.get("start_date")
    end_date_str = user_data.get("end_date")

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if start_date < date.today() and end_date < date.today():
        await callback.message.answer("Информация за этот период недоступна. "
                                      "Возможен поиск только предстоящих экскурсий. 😈")
        return

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    # Форматирование для вывода дат
    first_date = start_date.strftime('%d.%m.%Y')
    second_date = end_date.strftime('%d.%m.%Y')
    user_id = callback.from_user.id

    try:
        if is_superadmin(user_id):
            tours, errors = filter_for_sa_period(start_date, end_date)
        elif is_admin(user_id):
            tours, errors = filter_by_period(start_date, end_date)
        elif is_guide(user_id):
            tours, errors = filter_by_period(start_date, end_date, guide=user_id)
        else:
            await callback.answer("У вас нет прав для выполнения этой команды.")
            return
    except Exception as e:
        logger.error(f"Ошибка при загрузке экскурсий за период для {user_id}: {e}")
        await callback.message.answer("Произошла ошибка при обработке вашего запроса. Сообщите администратору.")
        return

    await send_tours_list(tours, errors, callback.message, first_date, second_date)

    # Сброс состояния
    await state.clear()


@router.callback_query(F.data == 'all_tours_pressed')
async def handle_all_tours(callback: CallbackQuery):
    """
    Обрабатывает запрос на показ всех экскурсий или экскурсий за период.
    Отправляет информацию из googlesheet обо всех экскурсиях за определённый период.
    """
    user_id = callback.from_user.id
    await callback.answer("Ищу все доступные туры ⏳")

    try:
        if is_superadmin(user_id):
            tours, errors = filter_for_sa_period()
        # Поиск экскурсий из гугл докса для админа
        elif is_admin(user_id):
            tours, errors = filter_by_period()
        # Поиск экскурсий из гугл докса для гидов
        elif is_guide(user_id):
            tours, errors = filter_by_period(guide=user_id)
        else:
            await callback.answer("У вас нет прав для выполнения этой команды.")
            return
    except Exception as e:
        logger.error(f"Ошибка при фильтрации экскурсий у {user_id}: {e}")
        await callback.message.answer("Произошла ошибка при обработке вашего запроса. Сообщите администратору.")
        return

    await send_tours_list(tours, errors, callback.message)
