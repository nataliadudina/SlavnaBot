import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

import bot.keyboards.keyboards as kb
from bot.filters.filters import IsAdmin
from bot.texts.staff_texts import buttons
from tripster.tparsing import handle_tripster

router = Router()
router.message.filter(IsAdmin())

logger = logging.getLogger(__name__)


# Только для администраторов
@router.message(F.text == buttons['extra'])
async def make_extra_keyboard(message: Message):
    """ При нажатии кнопки 'Дополнительно' создаются inline buttons с дальнейшим выбором. """
    await message.answer(text='Твой выбор',
                         reply_markup=kb.extra_keyboard)


@router.callback_query(F.data == 'tripster_pressed')
async def make_tripster_keyboard(callback: CallbackQuery):
    """
    Открывает новое inline подменю из кнопок для работы с Tripster.
    """
    await callback.answer("")
    await callback.message.edit_text(text='Что требуется?',
                                     reply_markup=kb.tripster_keyboard)


@router.callback_query(F.data == 'send_notes_pressed')
async def handle_tripster_regular(callback: CallbackQuery):
    """
     Запускает функцию отправки уведомлений на WhatsApp web.
    """
    await callback.answer(f"Начинаем рассылку.")

    try:
        messages_count = await handle_tripster()
        if messages_count:
            await callback.message.edit_text(
                text=f'Уведомления отправлены! Найдено заказов {messages_count}.',
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                text=f'Нет предстоящих экскурсий на выбранную дату.',
                reply_markup=None
            )
    except Exception as e:
        logger.error(f'Произошла ошибка во время отправки уведомлений: {e}')


@router.callback_query(F.data == 'late_orders_pressed')
async def handle_tripster_late(callback: CallbackQuery):
    """
     Запрашивает час (1 до 23), чтобы установить момент, с которого искать новые заказы
     для отправки уведомлений. После запускает функцию отправки уведомлений на WhatsApp web.
    """
    await callback.answer("")
    # await callback.message.
