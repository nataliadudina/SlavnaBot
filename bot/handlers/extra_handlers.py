import logging

from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import CallbackQuery, Message

import bot.keyboards.keyboards as kb
from bot.filters.filters import IsAdmin
from bot.handlers.date_handlers import DateInputState
from bot.handlers.period_handlers import DatesInputState
from bot.texts.staff_texts import buttons, tripster_text
from tripster.tparsing import handle_tripster

router = Router()
router.message.filter(IsAdmin())

logger = logging.getLogger(__name__)


# Состояние для ожидания часа
class HourInputState(StatesGroup):
    hour = State()


# Этот хэндлер срабатывает на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключает машину состояний
@router.message(Command(commands='cancel'), ~StateFilter(default_state))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == HourInputState.hour:
        await message.answer(
            text='Отправка уведомлений отменена.'
        )
    elif current_state in (DateInputState.due_date, DatesInputState.start_date, DatesInputState.end_date):
        await message.answer(
            text='Поиск экскурсий отменён.'
        )

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
