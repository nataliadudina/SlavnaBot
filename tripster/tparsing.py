from datetime import date, datetime, timedelta

from environs import Env

from tripster.services import send_message
from tripster.class_tparser import TParser

"""
Основной скрипт для парсера tripster.
Этот скрипт отвечает за:
1. Установку переменных окружения
2. Создание URL-адреса для запроса API исходя из ситуации: обычная рассылка или пришли новые заявки
3. Парсинг данных на ближайшие экскурсии
4. Отправка сообщений с разобранными данными
"""

# getting environs variables
env = Env()
env.read_env('.env')
token = env('TRIPSTER_TOKEN')


async def handle_tripster(update_hour: int = 20, day: str = 'tomorrow') -> int:
    now = datetime.now()
    update_time = now.replace(hour=update_hour, minute=00, second=0, microsecond=0)

    if now < update_time:
        # making regular messaging for orders made during last 3 months
        update_period = date.today() - timedelta(days=90)
        url = f"{env('TRIPSTER_URL')}?updated_after={update_period}"

    else:
        # making messaging for later orders
        date_str = str(update_time).split(' ')[0]
        time_str = str(update_time).split(' ')[1][:5]
        update_period_str = f'{date_str}%20{time_str}'  # adding time to url
        url = f"{env('TRIPSTER_URL')}?updated_after={update_period_str}"

    parser = TParser(url, token)
    msg_data = parser.get_tours_data(day)  # getting data for the message
    await send_message(msg_data)  # sending messages
    if msg_data:
        return len(msg_data)
    return 0
