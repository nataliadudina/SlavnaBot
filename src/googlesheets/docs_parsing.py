import logging

import gspread
from environs import Env

from src.config import config

env = Env()
env.read_env('.env')

logger = logging.getLogger(__name__)

gc = gspread.service_account(filename=config.credential_file)

# Opening a Google Sheet via a link
sheet_url = env('SPREADSHEET_URL')
sh = gc.open_by_url(sheet_url)

# Select sheet (by name or index)
worksheet = sh.worksheet('Заказы')


# Returns data from a table as a list of dicts.
# Each dict is a row of the table with keys in column order.
def get_orders() -> list[dict[str, int | float | str]]:
    # Loading all data in one request
    data = worksheet.get_all_records()
    if not data:
        logger.error('Гугл таблица пуста или недоступна.')
        raise ValueError("Таблица пуста или недоступна.")
    return data


# Cache data after loading
cached_data = get_orders()


# Detailed information on orders (12 columns) for admins
def get_extended_columns() -> list[str]:
    return list(cached_data[0].keys())[:12]


# Reduced information on orders (6 columns) for all
def get_brief_columns() -> list[str]:
    return list(cached_data[0].keys())[:6]


# Detailed information on orders (10 columns) for guides
def get_guides_columns() -> list[str]:
    headers = list(cached_data[0])
    return headers[:5] + headers[7:12]
