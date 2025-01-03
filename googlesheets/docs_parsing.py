import logging
import os

import gspread
from environs import Env
from google.oauth2.service_account import Credentials

env = Env()
env.read_env('.env')

logger = logging.getLogger(__name__)

# Путь к JSON-файлу с ключами
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'google_creds.json')

# Список областей авторизации
SCOPES = [env('SCOPES')]

# Настройка авторизации
credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

# Открытие Google Sheet по ссылке
sheet_url = env('SPREADSHEET_URL')
sh = gc.open_by_url(sheet_url)

# Выбор листа (по названию или индексу)
worksheet = sh.worksheet('Заказы')


# Возвращает данные из таблицы в виде списка словарей Python.
# Каждый словарь представляет собой строку таблицы с ключами в порядке столбцов.
def get_orders() -> list[dict[str, int | float | str]]:
    # Загружаем все данные в один запрос
    data = worksheet.get_all_records()
    if not data:
        logger.error('Гугл таблица пуста или недоступна.')
        raise ValueError("Таблица пуста или недоступна.")
    return data


# Кэшируем данные сразу после загрузки
cached_data = get_orders()


# Подробная информация о заказах (12 колонок) для админов
def get_extended_columns() -> list[str]:
    return list(cached_data[0].keys())[:12]


# Краткая информация о заказах (6 колонок) для всех
def get_brief_columns() -> list[str]:
    return list(cached_data[0].keys())[:6]


# Подробная информация о заказах для гидов (10 колонок)
def get_guides_columns() -> list[str]:
    headers = list(cached_data[0])
    return headers[:5] + headers[7:12]
