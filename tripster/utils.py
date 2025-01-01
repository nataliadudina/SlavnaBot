import logging
from datetime import date, datetime
from typing import Any
from urllib.parse import urlencode

import requests

excursions = {
    58872: '«К хозяйке Славенского конца»',
    61835: '«По Детинцу да по Пискупле»',
    65044: '«Айда на Славню — новыми маршрутами по Торговой стороне»'
}


def formate_date(dt: str) -> date:
    """ Форматирование даты. """
    return date.fromisoformat(dt)


def get_all_orders(base_url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    """
    Получение списка заказов со всех страниц с сегодняшней даты и позже.
    Вспомогательная функция для метода get_orders класса TParse.
    """

    all_orders = []
    current_page = 1  # Start page number for parsing
    next_page = True

    while next_page:
        params = {'page': current_page}
        url = f"{base_url}&{urlencode(params)}"

        response = requests.get(url, headers=headers)  # send a GET request to the API
        response.raise_for_status()  # raise exceptions for HTTP errors

        data = response.json()

        if 'results' in data:
            for order in data['results']:
                if order['event']['date'] and formate_date(order['event']['date']) >= date.today():
                    all_orders.append(order)

        # Get information about the existence of the next page
        next_page = data.get('next')

        logging.info(f"Received orders from page {current_page} ({len(all_orders)} orders.)")
        current_page += 1

    return sorted(all_orders, key=lambda d: d['event']['date'])


def form_data_for_message(all_data: list[dict]) -> list[dict[str, str]]:
    """
    Формирование списка словарей только с нужными данными:
    название экскурсии, дата, время, имя и телефон туриста, сумма к доплате
    для дальнейшего формирования сообщения.
    """

    data = []
    keys = ['tour', 'date', 'time', 'name', 'phone', 'amount']

    for order in all_data:
        excursion_id = order.get('experience_id')
        if excursion_id in excursions:
            tour = excursions[excursion_id]
        else:
            continue

        raw_date = datetime.strptime(order.get('event', {}).get('date'), '%Y-%m-%d')
        excursion_date = raw_date.strftime('%d.%m.%Y')
        time = order.get('event', {}).get('time')
        name = order.get('traveler', {}).get('name').split(' ')[0]
        phone = order.get('traveler', {}).get('phone')
        amount = order.get('price', {}).get('payment_to_guide')

        data.append(dict(zip(keys, [tour, excursion_date, time, name, phone, int(amount)])))
    return data
