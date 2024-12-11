import time

import pywhatkit

from tripster.texts import form_message


def send_message(data: list[dict]) -> None:
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

            pywhatkit.sendwhatmsg_instantly(phone_no=phone, message=message, tab_close=True)

            time.sleep(5)  # time for opening WhatsApp web in tab and send message

        except Exception as e:
            print(e)
