import asyncio
import logging

from pywhatkit import sendwhatmsg_instantly

from tripster.texts import form_message

logger = logging.getLogger(__name__)


async def send_message(data: list[dict]) -> None:
    """
    Эта функция отправляет уведомления туристам по WhatsApp.
    """

    # sending out messages
    for order in data:
        try:
            phone = order['phone']
            tour = order['tour']
            tour_date = order['date']
            tour_time = order['time']
            traveller_name = order['name']
            to_pay = order['amount']

            message = form_message(tour, traveller_name, tour_date, tour_time, to_pay)

            await asyncio.to_thread(sendwhatmsg_instantly, phone_no=phone, message=message, wait_time=5, tab_close=True,
                                    close_time=7)

        except Exception as e:
            logger.error(f'Произошла ошибка во время отправки уведомлений через WhatsApp web: {e}')
