import logging
from datetime import datetime, date

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

import bot.keyboards.keyboards as kb
from bot.filters.filters import is_admin, is_guide
from bot.keyboards.calendar import generate_calendar
from bot.texts.staff_texts import replies, buttons, tour_texts
from googlesheets.tours_filtering import filter_by_period, filter_by_guide_on_period

router = Router()

logger = logging.getLogger(__name__)


# Состояние для ожидания дат
class DatesInputState(StatesGroup):
    start_date = State()
    end_date = State()


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
    # Навигатор по календарю в модуле date_handlers.py
    keyboard = await generate_calendar(today.year, today.month, is_period=True)
    await callback.message.answer(text=f"Выберите первую дату.\n\n"
                                       f"{tour_texts['cancel_search']}",
                                  reply_markup=keyboard)
    await callback.answer()
    await state.set_state(DatesInputState.start_date)
    await state.update_data(is_period=True)


@router.callback_query(lambda c: c.data.startswith("navigate_"))
async def navigate_calendar(callback_query: CallbackQuery):
    """ Навигация по календарю: вперёд, назад. """
    _, year, month = callback_query.data.split("_")
    keyboard = await generate_calendar(int(year), int(month), is_period=True)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()


@router.callback_query(F.data.startswith('period_date_'), StateFilter(DatesInputState.start_date))
async def handle_start_date(callback: CallbackQuery, state: FSMContext):
    """ Обработка выбора начальной даты для периода. """
    start_date_str = callback.data.split('_')[2]
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    await state.update_data(start_date=start_date_str)

    # Показ выбранной даты и запрос конечной
    await callback.answer(f"{start_date.strftime('%d.%m.%Y')}. Выберете вторую дату.")

    today = datetime.today()
    keyboard = await generate_calendar(today.year, today.month, is_period=True)
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
    await callback.message.delete()

    # После выбора обеих дат можно продолжить обработку
    await handle_tours_by_period(callback, state)


@router.callback_query(F.data.startswith('period_date_') & F.state == DatesInputState.end_date)
async def handle_tours_by_period(callback: CallbackQuery, state: FSMContext):
    """ Обработка туров за выбранный период. """
    user_id = callback.from_user.id

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

    try:
        if is_admin(user_id):
            tours = filter_by_period(start_date, end_date)
        elif is_guide(user_id):
            tours = filter_by_guide_on_period(user_id, start_date, end_date)
        else:
            await callback.answer("У вас нет прав для выполнения этой команды.")
            return
    except Exception as e:
        logger.error(f"Ошибка при загрузке экскурсий за период для {user_id}: {e}")
        await callback.message.answer("Произошла ошибка при обработке вашего запроса. Попробуйте позже.")
        return

    if not tours:
        await callback.message.answer(f"Нет экскурсий с {first_date} по {second_date} 🥺")
        return

    await callback.message.answer(f'С {first_date} по {second_date} найдено экскурсий: {len(tours)}.')
    for row in tours:
        tour_info = "\n".join(f"<b>{header}</b>: {info}" for header, info in row.items())
        await callback.message.answer(tour_info)

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

    await callback.message.answer(f'Всего экскурсий: {len(tours)}')
