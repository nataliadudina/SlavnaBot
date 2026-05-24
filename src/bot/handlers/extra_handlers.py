import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import CallbackQuery, Message
from gspread.exceptions import APIError

import src.bot.keyboards.keyboards as kb
from src.googlesheets.make_record import add_record
from ..db.db import add_tour_to_db, is_tour_title_exists, get_tours_by_type, get_tour_by_id, update_tour, \
    update_tour_title, get_all_tours, delete_tour_from_db
from ..filters.filters import IsAdmin
from ..handlers.date_handlers import DateInputState
from ..handlers.period_handlers import DatesInputState
from ..texts.staff_texts import buttons, googledocs_text

router = Router()
router.message.filter(IsAdmin())

logger = logging.getLogger(__name__)


# ==================== States =====================


# State for Hour
class HourInputState(StatesGroup):
    hour = State()


# State for Order Record
class OrderInputState(StatesGroup):
    dt = State()
    tour_type = State()
    client_data = State()
    guides = State()
    price = State()
    guests = State()
    place = State()


# State for Adding Tour
class AddTourState(StatesGroup):
    title = State()
    description = State()


# State for Editing Tour
class EditTourState(StatesGroup):
    title = State()
    description = State()


# ==================== Helper funcs =====================


async def save_record(message: Message, state: FSMContext):
    """Recording data to Google Sheets."""
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
        await message.answer(f'⚠ Ошибка API Google Sheets. Попробуйте позже.')
        logger.error(f'⚠ Google Sheets API error: {e}. Please try again later.')
    except TypeError:
        await message.answer('❌ Ошибка формата данных. Проверьте ввод.')
    except Exception as e:
        logger.error(f'⚠ Unknown error while writing to Google Sheet: {e}')

    await state.clear()


# ==================== Cancel command =====================
# This handler triggers on the "/cancel" command in any state
# except the default state, and disables the state machine
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
        OrderInputState.guests: 'Добавление экскурсии отменено.',
        AddTourState.title: 'Добавление экскурсии отменено.'
    }

    if current_state in cancel_messages:
        await message.answer(text=cancel_messages[current_state])

    await state.clear()


# ==================== 'Дополнительно' button =====================
@router.message(F.text == buttons['extra'])
async def make_extra_keyboard(message: Message):
    """ When the 'Дополнительно' button is clicked, inline buttons are created for further selection. """
    await message.answer(text='Ваш выбор',
                         reply_markup=kb.extra_keyboard)


# Submenus
@router.callback_query(F.data == 'excursions_pressed')
async def excursions_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        buttons['handle_tours'],
        reply_markup=kb.excursions_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == 'add_tour_pressed')
async def add_tour_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        'Что добавить?',
        reply_markup=kb.add_tour_type,
    )
    await callback.answer()


@router.callback_query(F.data == 'edit_tour_pressed')
async def edit_tour_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        'Что редактировать?',
        reply_markup=kb.edit_tour_type,
    )
    await callback.answer()


# Back buttons
@router.callback_query(F.data == 'back_to_extra')
async def back_to_extra_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        buttons['extra'],
        reply_markup=kb.extra_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == 'back_to_excursions')
async def back_to_excursions_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        buttons['handle_tours'],
        reply_markup=kb.excursions_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == 'back_to_types')
async def back_to_types_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        'Что редактировать?',
        reply_markup=kb.edit_tour_type,
    )
    await callback.answer()


@router.callback_query(F.data == 'back_to_list')
async def back_to_list_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    data = await state.get_data()
    tour_type = data.get('edit_tour_type')

    if not tour_type:
        # fallback
        await callback.message.edit_text(
            'Что редактировать?',
            reply_markup=kb.edit_tour_type,
        )
        await callback.answer()
        return

    tours = await get_tours_by_type(tour_type)

    await callback.message.edit_text(
        buttons['choose_tour'],
        reply_markup=kb.edit_tours_list_keyboard(tours),
    )
    await callback.answer()


# ==================== Writing to Google Doc =====================
@router.message(Command(commands='log'), ~StateFilter(default_state))
async def cmd_log(message: Message, state: FSMContext):
    """ Handler for interrupting the survey and calling the function to save the excursion to a GoogleSheet."""
    await save_record(message, state)


@router.callback_query(F.data == 'gdocs_pressed')
async def ask_for_datetime(callback: CallbackQuery, state: FSMContext):
    """ Requests date and time."""
    await callback.message.edit_text(
        text=googledocs_text['datetime'],
        reply_markup=None
    )
    await state.set_state(OrderInputState.dt)


@router.message(OrderInputState.dt)
async def get_datetime(message: Message, state: FSMContext):
    """ Date & time validation."""
    date_text = message.text.strip()
    date_formats = ["%d.%m.%Y %H:%M", "%d.%m.%y %H:%M"]
    for fmt in date_formats:
        try:
            new_datetime = datetime.strptime(date_text, fmt)

            # if year is like '26'
            if new_datetime.year < 2000:
                new_datetime = new_datetime.replace(year=new_datetime.year + 2000)

            if new_datetime < datetime.now():
                await message.answer("❌ Укажите корректную дату: она не может быть прошедшей.")
                return

            await state.update_data(new_datetime=new_datetime)
            await message.answer(text=googledocs_text['tour_type'],
                                 reply_markup=None)
            await state.set_state(OrderInputState.tour_type)
            return

        except ValueError:
            continue

    await message.answer(
        "❌ Неверный формат. Введите дату и время в формате:\n"
        "• ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "• ДД.ММ.ГГ ЧЧ:ММ"
    )


@router.message(OrderInputState.tour_type)
async def get_tour_type(message: Message, state: FSMContext):
    """Handles the selection of the tour type: an item from the list or custom text."""
    tour_type = message.text.strip()

    if tour_type.isdigit() and not 1 <= int(tour_type) <= 7:
        await message.answer("❌ Неверный номер программы. Выберите число от 1 до 7")
        return

    await state.update_data(tour_type=tour_type)
    await message.answer(text=googledocs_text['client_data'],
                         reply_markup=None)
    await state.set_state(OrderInputState.client_data)


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
    """Writes a new entry to the Google Doc after the last question."""
    await state.update_data(place=message.text)
    await save_record(message, state)


# ==================== Adding excursion =====================
@router.callback_query(F.data == 'add_on_request')
async def add_individual_tour(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()
    await state.update_data(tour_type='individual')
    await state.set_state(AddTourState.title)

    await callback.message.answer(
        'Введите название индивидуальной экскурсии'
    )
    await callback.answer()


@router.callback_query(F.data == 'add_in_group')
async def add_group_tour(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()
    await state.update_data(tour_type='group')
    await state.set_state(AddTourState.title)

    await callback.message.answer(
        'Введите название сборной экскурсии'
    )
    await callback.answer()


@router.message(AddTourState.title)
async def add_tour_title(
        message: Message,
        state: FSMContext,
):
    title = message.text.strip()

    if not title or len(title) > 50:
        await message.answer(
            'Название должно быть непустым и не длиннее 50 символов. Попробуйте ещё раз.'
        )
        return

    data = await state.get_data()
    tour_type = data.get('tour_type')

    if await is_tour_title_exists(title, tour_type):
        await message.answer(
            'Экскурсия с таким названием уже существует.\n'
            'Пожалуйста, введите другое название или нажмите /cancel для выхода.'
        )
        return

    await state.update_data(title=title)
    await state.set_state(AddTourState.description)

    await message.answer(
        'Введите описание экскурсии'
    )


@router.message(AddTourState.description)
async def add_tour_description(
        message: Message,
        state: FSMContext,
):
    description = message.text.strip()

    if not description:
        await message.answer(
            'Описание не может быть пустым. Попробуйте ещё раз.'
        )
        return

    data = await state.get_data()

    success = await add_tour_to_db(
        title=data['title'],
        description=description,
        tour_type=data['tour_type'],
    )

    await state.clear()

    if success:
        await message.answer(
            '✅ Экскурсия успешно добавлена',
            reply_markup=kb.excursions_keyboard,
        )
    else:
        await message.answer(
            '⚠️ Не удалось сохранить экскурсию. Попробуйте позже.',
            reply_markup=kb.excursions_keyboard,
        )


# ==================== Editing excursion =====================
@router.callback_query(F.data.in_({'edit_on_request', 'edit_in_group'}))
async def edit_tours_list(
        callback: CallbackQuery,
        state: FSMContext,
):
    tour_type = (
        'individual'
        if callback.data == 'edit_on_request'
        else 'group'
    )

    tours = await get_tours_by_type(tour_type)

    if not tours:
        await callback.answer(
            'Экскурсий этого типа пока нет.',
            show_alert=True
        )
        return

    await state.clear()
    await state.update_data(edit_tour_type=tour_type)

    await callback.message.edit_text(
        buttons['choose_tour'],
        reply_markup=kb.edit_tours_list_keyboard(tours),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('edit_tour_select:'))
async def edit_tour_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    tour_id = int(callback.data.split(':')[1])

    await callback.message.edit_text(
        'Что вы хотите изменить?',
        reply_markup=kb.edit_tour_actions_keyboard(tour_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('edit_tour_title:'))
async def edit_tour_title_start(
        callback: CallbackQuery,
        state: FSMContext,
):
    tour_id = int(callback.data.split(':')[1])

    tour = await get_tour_by_id(tour_id)
    if not tour:
        await callback.answer('Экскурсия не найдена', show_alert=True)
        return

    await state.clear()
    await state.update_data(edit_tour_id=tour_id)
    await state.set_state(EditTourState.title)

    await callback.message.edit_text(
        f'Текущее название:\n'
        f'«{tour["title"]}»\n\n'
        f'Введите новое название:',
    )
    await callback.answer()


@router.callback_query(F.data.startswith('edit_tour_description:'))
async def edit_tour_description_start(
        callback: CallbackQuery,
        state: FSMContext,
):
    tour_id = int(callback.data.split(':')[1])

    tour = await get_tour_by_id(tour_id)
    if not tour:
        await callback.answer('Экскурсия не найдена', show_alert=True)
        return

    await state.clear()
    await state.update_data(
        edit_tour_id=tour_id,
    )
    await state.set_state(EditTourState.description)

    await callback.message.edit_text(
        f'Текущее описание:\n'
        f'{tour["description"]}\n\n'
        f'Введите новое описание:',
    )
    await callback.answer()


@router.message(EditTourState.title)
async def edit_tour_title_save(
        message: Message,
        state: FSMContext,
):
    new_title = message.text.strip()

    if not new_title:
        await message.answer('Название не может быть пустым')
        return

    data = await state.get_data()
    tour_id = data['edit_tour_id']

    await update_tour_title(tour_id, new_title)

    await message.answer(
        '✅ Название экскурсии обновлено',
        reply_markup=kb.edit_tour_actions_keyboard(tour_id),
    )


@router.message(EditTourState.description)
async def edit_tour_description_save(
        message: Message,
        state: FSMContext,
):
    new_description = message.text.strip()

    if not new_description:
        await message.answer(
            'Описание не может быть пустым.'
        )
        return

    data = await state.get_data()
    tour_id = data['edit_tour_id']

    await update_tour(tour_id, new_description)

    await state.clear()

    await message.answer(
        '✅ Описание экскурсии обновлено',
        reply_markup=kb.edit_tour_actions_keyboard(tour_id),
    )


# ==================== Deleting excursion ====================
@router.callback_query(F.data == 'delete_tour_pressed')
async def delete_tour_menu(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    tours = await get_all_tours()

    if not tours:
        await callback.answer(
            'Нет экскурсий.',
            show_alert=True
        )
        return

    await callback.message.edit_text(
        'Что удалить?',
        reply_markup=kb.delete_tour_list(tours),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('delete_tour_select:'))
async def delete_tour_select(
        callback: CallbackQuery,
        state: FSMContext,
):
    tour_id = int(callback.data.split(':')[1])

    tour = await get_tour_by_id(tour_id)
    if not tour:
        await callback.answer('Экскурсия не найдена', show_alert=True)
        return

    await state.clear()
    await state.update_data(delete_tour_id=tour_id)

    await callback.message.edit_text(
        f'⚠️ Вы действительно хотите удалить экскурсию:\n'
        f'«{tour["title"]}»?',
        reply_markup=kb.delete_tour_confirm_keyboard(tour_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('delete_tour_confirm:'))
async def delete_tour_confirm(
        callback: CallbackQuery,
        state: FSMContext,
):
    tour_id = int(callback.data.split(':')[1])

    await delete_tour_from_db(tour_id)

    await state.clear()

    tours = await get_all_tours()

    if not tours:
        await callback.message.edit_text(
            'Экскурсий больше нет',
            reply_markup=kb.excursions_keyboard,
        )
    else:
        await callback.message.edit_text(
            'Экскурсия удалена. Что ещё удалить?',
            reply_markup=kb.delete_tour_list(tours),
        )

    await callback.answer('Удалено')


@router.callback_query(F.data == 'delete_tour_cancel')
async def delete_tour_cancel(
        callback: CallbackQuery,
        state: FSMContext,
):
    await state.clear()

    tours = await get_all_tours()

    await callback.message.edit_text(
        'Что удалить?',
        reply_markup=kb.delete_tour_list(tours),
    )
    await callback.answer()
