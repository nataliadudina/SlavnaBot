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

# Открытие Google Sheet по ссылкам
sheet_urls = {
    'Маркова': env('SPREADSHEET_M_URL'),
    'Путятина': env('SPREADSHEET_P_URL')
}

worksheets = {
    name: gc.open_by_url(url).worksheet(name)
    for name, url in sheet_urls.items()
}


# Функция для получения данных из листа
def get_extra_orders(sheet_name: str) -> list[dict[str, int | float | str]]:
    worksheet = worksheets[sheet_name]
    data = worksheet.get_all_records()
    if not data:
        logger.error(f"Гугл таблица '{sheet_name}' пуста или недоступна.")
        raise ValueError(f"Таблица '{sheet_name}' пуста или недоступна.")
    return data


# Кэшируем данные для всех листов
cached_data = {
    name: get_extra_orders(name) for name in worksheets
}


# Функция для получения колонок
def get_columns(sheet_name: str, column_ranges: list[tuple[int, int]]) -> list[str]:
    headers = list(cached_data[sheet_name][0])
    return [
        header
        for start, end in column_ranges
        for header in headers[start:end]
    ]


# Получение данных для Марковой
def get_admin_mcolumns() -> list[str]:
    return get_columns('Маркова', [(0, 5), (6, 7), (8, 9)])


def get_m_columns() -> list[str]:
    return get_columns('Маркова', [(0, 3), (4, 7), (8, 9)])


# Получение данных для Путятиной
def get_admin_pcolumns() -> list[str]:
    return get_columns('Путятина', [(0, 5), (6, 7), (8, 9)])


def get_p_columns() -> list[str]:
    return get_columns('Путятина', [(0, 3), (4, 7), (8, 10)])

