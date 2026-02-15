import logging

import gspread
from environs import Env

from src.config import config

env = Env()
env.read_env('.env')

logger = logging.getLogger(__name__)

gc = gspread.service_account(filename=config.credential_file)

# Opening a Google Sheet via a links
sheet_urls = {
    'Маркова': env('SPREADSHEET_M_URL'),
    'Путятина': env('SPREADSHEET_P_URL')
}

worksheets = {
    name: gc.open_by_url(url).worksheet(name)
    for name, url in sheet_urls.items()
}


# Get data from google sheet
def get_extra_orders(sheet_name: str) -> list[dict[str, int | float | str]]:
    worksheet = worksheets[sheet_name]
    data = worksheet.get_all_records()
    if not data:
        logger.error(f"Гугл таблица '{sheet_name}' пуста или недоступна.")
        raise ValueError(f"Таблица '{sheet_name}' пуста или недоступна.")
    return data


# Cash data
cached_data = {
    name: get_extra_orders(name) for name in worksheets
}


# Get columns
def get_columns(sheet_name: str, column_ranges: list[tuple[int, int]]) -> list[str]:
    headers = list(cached_data[sheet_name][0])
    return [
        header
        for start, end in column_ranges
        for header in headers[start:end]
    ]


# Get data for Маркова
def get_admin_mcolumns() -> list[str]:
    return get_columns('Маркова', [(0, 5), (6, 7), (8, 9)])


# All columns for Маркова
def get_m_columns() -> list[str]:
    return get_columns('Маркова', [(0, 3), (4, 7), (8, 9)])


# Get data for Путятина
def get_admin_pcolumns() -> list[str]:
    return get_columns('Путятина', [(0, 5), (6, 7), (8, 9)])


# All columns for Путятина
def get_p_columns() -> list[str]:
    return get_columns('Путятина', [(0, 3), (4, 7), (8, 10)])


# Reduced columns for both guids
def get_brief_mpcols() -> list[str]:
    return get_columns('Путятина', [(0, 3), (6, 7)])
