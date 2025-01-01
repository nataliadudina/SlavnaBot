import logging
from datetime import date, timedelta

import requests

from tripster.utils import form_data_for_message, get_all_orders

logging.basicConfig(level=logging.INFO)


class TParser:
    """ Класс для парсинга заказов с Трипстера """

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Token {self.token}",
        }

    def get_orders(self) -> list[dict]:
        """
        Получение списка всех будущих заказов, учитывая сегодня.
        Базовый метод.
        """

        try:
            all_orders = get_all_orders(self.base_url, headers=self.headers)
            logging.info(f'Total orders found: {len(all_orders)}.')
            return all_orders
        except requests.RequestException as e:
            logging.warning(f"Ошибка при получении данных: {e}")
            return []

    def get_today_tours(self) -> list[dict] | str:
        """
        Получение списка оплаченных заказов на сегодня.
        Фильтруются заказы из метода get_orders.
        """

        next_tour_data = self.get_orders()
        next_tours = []
        for order in next_tour_data:
            tour_date = date.fromisoformat(order['event']['date'])
            if order['status'] == 'paid' and tour_date - date.today() == timedelta(days=0):
                next_tours.append(order)
        logging.info(f'Found {len(next_tours)} orders for today.')
        return next_tours

    def get_tomorrow_tours(self) -> list[dict] | str:
        """
        Получение списка оплаченных заказов на завтра.
        Фильтруются заказы из метода get_orders.
        """

        next_tour_data = self.get_orders()
        next_tours = []
        for order in next_tour_data:
            tour_date = date.fromisoformat(order['event']['date'])
            if order['status'] == 'paid' and tour_date - date.today() == timedelta(days=1):
                next_tours.append(order)
        logging.info(f'Found {len(next_tours)} orders for tomorrow.')
        return next_tours

    def get_tours_data(self, day='tomorrow') -> list[dict]:
        """
        Получение списка словарей только с нужными данными:
        название экскурсии, дата, время, имя и телефон туриста, сумма к доплате
        для дальнейшего формирования сообщения.
        Используется метод get_next_tours для получения списка ближайших экскурсий.
        """
        if day == 'today':
            orders = self.get_today_tours()
        else:
            orders = self.get_tomorrow_tours()
        data = form_data_for_message(orders)  # get data for messages sending
        return data
