import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import CallbackQuery, Message
from gspread.exceptions import APIError

import bot.keyboards.keyboards as kb
from bot.filters.filters import IsAdmin
from bot.handlers.date_handlers import DateInputState
from bot.handlers.period_handlers import DatesInputState
from bot.texts.staff_texts import buttons, tripster_text, googledocs_text
from googlesheets.make_record import add_record
from tripster.tparsing import handle_tripster

router = Router()
router.message.filter(IsAdmin())

logger = logging.getLogger(__name__)


# Состояние для ожидания часа
class HourInputState(StatesGroup):
    hour = State()


# Состояние для записи заказа
class OrderInputState(StatesGroup):
    dt = State()
    tour_type = State()
    client_data = State()
    guides = State()
    price = State()
    guests = State()
    place = State()


async def save_record(message: Message, state: FSMContext):
    """Функция для записи данных в Google Sheets."""
    record_data = await state.get_data()

    new_record = [
        record_data.get('new_datetime').strftime('%d.%m.%Y'),
        record_data.get('new_datetime').strftime('%H:%M'),
        record_data.get('tour_type', ''),
        record_data.get('client_data', ''),
        record_data.get('guides', ''),
        record_data.get('price', ''),
        record_data.get('guests', ''),
        record_data.get('place', ''),
    ]

    try:
        add_record(new_record)
        await message.answer('✅ Запись успешно добавлена в Google Doc!')
    except APIError as e:
        await message.answer(f'⚠ Ошибка API Google Sheets: {e}. Попробуйте позже.')
    except TypeError:
        await message.answer('❌ Ошибка формата данных. Проверьте ввод.')
    except Exception as e:
        logger.error(f'⚠ Неизвестная ошибка при записи в Google Sheet: {e}')

    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


@router.message(OrderInputState.place)
async def write_to_googledoc(message: Message, state: FSMContext):
    """Записывает в Google Sheets новую запись после последнего вопроса."""
    await state.update_data(place=message.text)
    await save_record(message, state)


# Этот хэндлер срабатывает на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключает машину состояний
@router.message(Command(commands='cancel'), ~StateFilter(default_state))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()

    cancel_messages = {
        HourInputState.hour: 'Отправка уведомлений отменена.',
        DateInputState.due_date: 'Поиск экскурсий отменён.',
        DatesInputState.start_date: 'Поиск экскурсий отменён.',
        DatesInputState.end_date: 'Поиск экскурсий отменён.',
        OrderInputState.dt: 'Добавление экскурсии отменено.',
        OrderInputState.tour_type: 'Добавление экскурсии отменено.',
        OrderInputState.client_data: 'Добавление экскурсии отменено.',
        OrderInputState.guides: 'Добавление экскурсии отменено.',
        OrderInputState.price: 'Добавление экскурсии отменено.',
        OrderInputState.guests: 'Добавление экскурсии отменено.'
    }

    if current_state in cancel_messages:
        await message.answer(text=cancel_messages[current_state])

    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


# Только для администраторов
@router.message(F.text == buttons['extra'])
async def make_extra_keyboard(message: Message):
    """ При нажатии кнопки 'Дополнительно' создаются inline buttons с дальнейшим выбором. """
    await message.answer(text='Ваш выбор',
                         reply_markup=kb.extra_keyboard)


@router.callback_query(F.data == 'tripster_pressed')
async def make_tripster_keyboard(callback: CallbackQuery):
    """
    Открывает новое inline подменю из кнопок для работы с Tripster.
    """
    await callback.answer("")
    await callback.message.edit_text(text='Что требуется?',
                                     reply_markup=kb.tripster_keyboard)


@router.callback_query(F.data == 'send_tdy_pressed')
async def handle_tripster_today(callback: CallbackQuery):
    """
     Запускает функцию отправки уведомлений на сегодняшние экскурсии через WhatsApp web.
    """
    await callback.answer(f"Начинаем рассылку 📩")

    try:
        messages_count = await handle_tripster(day='today')
        if messages_count:
            await callback.message.edit_text(
                text=f'Уведомления отправлены! Найдено заказов {messages_count}.',
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                text=tripster_text['no_tripster'],
                reply_markup=None
            )
    except Exception as e:
        logger.error(f'Произошла ошибка во время отправки уведомлений: {e}')


@router.callback_query(F.data == 'send_tmrw_pressed')
async def handle_tripster_tomorrow(callback: CallbackQuery):
    """
     Запускает функцию отправки уведомлений на завтрашние экскурсии через WhatsApp web.
    """
    await callback.answer(f"Начинаем рассылку 📩")

    try:
        messages_count = await handle_tripster(day='tomorrow')
        if messages_count:
            await callback.message.edit_text(
                text=f'Уведомления отправлены! Найдено заказов {messages_count}.',
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                text=tripster_text['no_tripster'],
                reply_markup=None
            )
    except Exception as e:
        logger.error(f'Произошла ошибка во время отправки уведомлений: {e}')


@router.callback_query(F.data == 'late_orders_pressed')
async def handle_tripster_late(callback: CallbackQuery, state: FSMContext):
    """
     Запрашивает час (1 до 23), чтобы установить момент, с которого искать новые заказы
     для отправки уведомлений. После запускает функцию отправки уведомлений на WhatsApp web.
    """
    await callback.message.edit_text(
        text=tripster_text['name_hour'],
        reply_markup=None
    )
    await state.set_state(HourInputState.hour)


@router.message(StateFilter(HourInputState.hour), lambda h: h.text.isdigit() and 1 <= int(h.text) <= 23)
async def handle_hour_input(message: Message, state: FSMContext):
    """
    Обрабатывает ввод пользователя и запускает функцию с переданным аргументом.
    """
    try:
        hour = int(message.text)

        await message.answer(f"Начинаем рассылку 📩")

        messages_count = await handle_tripster(update_hour=hour, day='today')
        if messages_count:
            await message.answer(
                text=f'Уведомления отправлены! Найдено заказов {messages_count}.'
            )
        else:
            await message.answer(
                text=tripster_text['no_tripster']
            )
    except Exception as e:
        logger.error(f'Произошла ошибка во время отправки уведомлений: {repr(e)}')
    finally:
        await state.clear()


@router.message(StateFilter(HourInputState.hour))
async def handle_incorrect_hour_input(message: Message):
    """
    Обрабатывает некорректный ввод пользователя и просит ввести число ещё раз.
    """
    await message.answer(
        text=tripster_text['incorrect_hour']
    )


@router.callback_query(F.data == 'gdocs_pressed')
async def ask_for_datetime(callback: CallbackQuery, state: FSMContext):
    """ Запрашивает дату и время для записи."""
    await callback.message.edit_text(
        text=googledocs_text['datetime'],
        reply_markup=None
    )
    await state.set_state(OrderInputState.dt)


@router.message(OrderInputState.dt)
async def get_datetime(message: Message, state: FSMContext):
    try:
        date_text = message.text
        if len(date_text.split()[0].split('.')[2]) == 2:  # если год состоит из двух цифр
            date_text = date_text.replace(date_text.split()[0].split('.')[2], '20' + date_text.split()[0].split('.')[2])

        new_datetime = datetime.strptime(date_text, "%d.%m.%Y %H:%M")

        await state.update_data(new_datetime=new_datetime)
        await message.answer(text=googledocs_text['tour_type'],
                             reply_markup=None)
        await state.set_state(OrderInputState.tour_type)
    except ValueError:
        await message.answer("❌ Неверный формат. Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ или ДД.ММ.ГГ ЧЧ:ММ")
        return


@router.message(OrderInputState.tour_type)
async def get_tour_type(message: Message, state: FSMContext):
    await state.update_data(tour_type=message.text)
    await message.answer(text=googledocs_text['client_data'],
                         reply_markup=None)
    await state.set_state(OrderInputState.client_data)

    # try:
    #     tour_type = int(message.text)
    #     if not (1 <= tour_type <= 7):
    #         await message.answer("❌ Неверный номер программы. Выберите число от 1 до 7")
    #         return
    #     await state.update_data(tour_type=tour_type)
    #     await message.answer(text=googledocs_text['client_data'],
    #                          reply_markup=None)
    #     await state.set_state(OrderInputState.client_data)
    # except ValueError:
    #     await message.answer("❌ Неверный номер программы. Выберите число от 1 до 7")
    #     return


@router.message(Command(commands='log'), ~StateFilter(default_state))
async def cmd_log(message: Message, state: FSMContext):
    """ Хендлер для прерывания опроса и вызова функции записи экскурсии в докс."""
    await save_record(message, state)


@router.message(OrderInputState.client_data)
async def add_client_data(message: Message, state: FSMContext):
    await state.update_data(client_data=message.text)
    await message.answer(text=googledocs_text['guides'],
                         reply_markup=None)
    await state.set_state(OrderInputState.guides)


@router.message(OrderInputState.guides)
async def add_guides(message: Message, state: FSMContext):
    await state.update_data(guides=message.text)
    await message.answer(text=googledocs_text['price'],
                         reply_markup=None)
    await state.set_state(OrderInputState.price)


@router.message(OrderInputState.price)
async def add_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer(text=googledocs_text['guests'],
                         reply_markup=None)
    await state.set_state(OrderInputState.guests)


@router.message(OrderInputState.guests)
async def add_guides(message: Message, state: FSMContext):
    await state.update_data(guests=message.text)
    await message.answer(text=googledocs_text['place'],
                         reply_markup=None)
    await state.set_state(OrderInputState.place)


@router.message(OrderInputState.place)
async def write_to_googledoc(message: Message, state: FSMContext):
    """Записывает в google doc новую запись."""
    await state.update_data(place=message.text)
    await save_record(message, state)
