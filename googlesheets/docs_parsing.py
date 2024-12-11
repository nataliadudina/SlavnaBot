import os

import gspread
from environs import Env
from google.oauth2.service_account import Credentials

env = Env()
env.read_env('.env')

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
def get_orders():
    return worksheet.get_all_records()


# Подробная информация о заказах (12 колонок)
def get_extended_columns():
    return [worksheet.col_values(i)[0] for i in range(1, 13)]


# Краткая информация о заказах (6 колонок)
def get_brief_columns():
    return [worksheet.col_values(i)[0] for i in range(1, 7)]


# Подробная информация о заказах для гидов (12 колонок)
def get_guides_columns():
    return [
        *[worksheet.col_values(i)[0] for i in range(1, 6)],
        *[worksheet.col_values(i)[0] for i in range(8, 13)],
    ]
