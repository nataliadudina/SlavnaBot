import logging
import re
from datetime import datetime, date
from typing import Optional

from googlesheets.docs_parsing import get_extended_columns, get_brief_columns, get_guides_columns, cached_data

logger = logging.getLogger(__name__)

# Telegram ids гидов
GUIDES = {
    5148077067: 'Забава',
    5148077068: 'Агафья',
    5148077066: 'Феофания'
}

# Предкомпилированные паттерны для фильтрации
GUIDE_PATTERNS = {id_: re.compile(rf'\b{name}\b', re.IGNORECASE) for id_, name in GUIDES.items()}


def format_date(str_date: str) -> date:
    # Функция для форматирования даты
    try:
        pattern = '%d.%m.%Y'
        return datetime.strptime(str_date, pattern).date()
    except (ValueError, TypeError):
        pass


def filter_by_date(
        due_date: Optional[date] = None
) -> list[dict] | None:
    """
    Фильтрует данные из google sheet по дате.

    Если due_date передан, фильтрует данные за указанную дату.
    В противном случае фильтрует данные за сегодняшнюю дату.

    Args:
        due_date (Optional[date], optional): Дата для фильтрации. Если не указано, используется текущая дата.

    Returns:
        Optional[List[Dict[str, Any]]]: Фильтрованные данные или None в случае ошибки.
    """
    try:
        # Дата для фильтрации
        tour_date = due_date if due_date else date.today()

        # Получаем доступ к гугл-таблице и отбираем нужные колонки
        data = cached_data
        columns = get_extended_columns()

        filtered_data = [
            {header: info for header, info in row.items() if header in columns and info}
            for row in data
            if (date_value := format_date(row.get('Дата'))) and date_value == tour_date
        ]
        return filtered_data
    except Exception as e:
        logger.error(f"Ошибка при загрузке или фильтрации данных: {e}")
        return None


def filter_by_period(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
) -> list[dict] | None:
    """
    Фильтрует данные из google sheet за указанный период.

    Если обе даты переданы, фильтрует данные за указанный период.
    В противном случае фильтрует данные с текущей даты до конца списка.

    Args:
        start_date (Optional[date], optional): Начальная дата для фильтрации. Если не указано, используется текущая дата
        end_date (Optional[date], optional): Конечная дата для фильтрации. Если не указано, используется конец списка.

    Returns:
        Optional[List[Dict[str, Any]]]: Фильтрованные данные или None в случае ошибки.
    """
    try:
        # Получаем данные из гугл-таблице и отбираем нужные колонки
        data = cached_data
        columns = get_brief_columns()

        # Фильтрация данных на период
        if start_date and end_date:
            filtered_data = [
                {header: info for header, info in row.items() if header in columns and info}
                for row in data
                if (date_value := format_date(row.get('Дата'))) and start_date <= date_value <= end_date
            ]

        # Фильтрация данных с сегодняшнего дня
        else:
            filtered_data = [
                {header: info for header, info in row.items() if header in columns and info}
                for row in data
                if (date_value := format_date(row.get('Дата'))) and date_value >= date.today()
            ]
        return filtered_data
    except Exception as e:
        logger.error(f"Ошибка при загрузке или фильтрации данных: {e}")
        return None


def filter_by_guide_on_date(
        guide: int,
        due_date: Optional[date] = None
) -> list[dict] | None:
    """
    Фильтрует данные из google sheet на дату и по гиду.

    Если due_date передан, фильтрует данные за указанную дату.
    В противном случае фильтрует данные за сегодняшнюю дату.

    Args:
        guide (int): Id гида для фильтрации его экскурсий.
        due_date (Optional[date], optional): Дата для фильтрации. Если не указано, используется текущая дата.

    Returns:
        Optional[List[Dict[str, Any]]]: Фильтрованные данные или None в случае ошибки.
    """
    try:
        # Получаем данные из гугл-таблице и отбираем нужные колонки
        data = cached_data
        columns = get_guides_columns()

        # Дата для фильтрации
        tour_date = due_date if due_date else date.today()
        # Паттерн для фильтрации экскурсий по гиду
        guide_pattern = GUIDE_PATTERNS.get(guide)

        # Фильтрация данных на дату
        filtered_data = [
            {header: info for header, info in row.items() if header in columns and info}
            for row in data
            if (date_value := format_date(row.get('Дата'))) and date_value == tour_date and (
                    guide_pattern.search(row.get('Герой').strip()) or guide_pattern.search(
                row.get('Второй герой').strip()))
        ]
        return filtered_data
    except Exception as e:
        logger.error(f"Ошибка при загрузке или фильтрации данных: {e}")
        return None


def filter_by_guide_on_period(
        guide: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
) -> list[dict] | None:
    """
    Фильтрует данные из google sheet за указанный период.

    Если обе даты переданы, фильтрует данные за указанный период.
    В противном случае фильтрует данные с текущей даты до конца списка.

    Args:
        guide (int): Id гида для фильтрации его экскурсий.
        start_date (Optional[date], optional): Начальная дата для фильтрации. Если не указано, используется текущая дата
        end_date (Optional[date], optional): Конечная дата для фильтрации. Если не указано, используется конец списка.

    Returns:
        Optional[List[Dict[str, Any]]]: Фильтрованные данные или None в случае ошибки.
    """
    try:
        # Получаем данные из гугл-таблице и отбираем нужные колонки
        data = cached_data
        columns = get_brief_columns()

        # Паттерн для фильтрации экскурсий по гиду
        guide_pattern = GUIDE_PATTERNS.get(guide)

        # Фильтрация данных на период
        if start_date and end_date:
            filtered_data = [
                {header: info for header, info in row.items() if header in columns and info}
                for row in data
                if (date_value := format_date(row.get('Дата'))) and start_date <= date_value <= end_date and (
                        guide_pattern.search(row.get('Герой').strip()) or guide_pattern.search(
                    row.get('Второй герой').strip()))
            ]

        # Фильтрация данных с сегодняшнего дня
        else:
            filtered_data = [
                {header: info for header, info in row.items() if header in columns and info}
                for row in data
                if (date_value := format_date(row.get('Дата'))) and date_value >= date.today() and (
                        guide_pattern.search(row.get('Герой').strip()) or guide_pattern.search(
                    row.get('Второй герой').strip()))
            ]
        return filtered_data
    except Exception as e:
        logger.error(f"Ошибка при загрузке или фильтрации данных: {e}")
        return None
