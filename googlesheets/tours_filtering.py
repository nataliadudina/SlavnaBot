import logging
from datetime import datetime, date
from difflib import get_close_matches
from typing import Optional

from environs import Env

from googlesheets.docs_parsing import get_brief_columns, get_guides_columns, get_orders, get_extended_columns
from googlesheets.mydocs_parsing import get_m_columns, get_p_columns, get_extra_orders, get_brief_mpcols

logger = logging.getLogger(__name__)

env = Env()
env.read_env('.env')

# =================== Constants ===================
# Guides' ids
zabava = int(env('ZABAVA'))
agafya = int(env('AGAFYA'))
feofaniya = int(env('FEOFANIYA'))

GUIDES = {
    zabava: {'name': 'Забава', 'surname': 'Путятина'},
    agafya: {'name': 'Агафья', 'surname': 'Селиванова'},
    feofaniya: {'name': 'Феофания', 'surname': 'Маркова'}
}


# =================== Helper functions ===================
def format_date(str_date: str) -> date:
    """ Функция для форматирования даты """
    try:
        pattern = '%d.%m.%Y'
        return datetime.strptime(str_date, pattern).date()
    except (ValueError, TypeError):
        pass


def sort_tours(data: list[dict]) -> list[dict]:
    """ Сортирует данные экскурсий по дате и времени. """
    return sorted(
        data,
        key=lambda k: (
            format_date(k['Дата']),
            datetime.strptime(k['Время'], '%H:%M')
        )
    )


def guide_mentioned_with_typos(row: dict, guide_id: int) -> bool:
    """
    Проверяет, упоминается ли гид в строке row (в полях 'Герой' и 'Второй герой'),
    с учётом возможных опечаток.
    """
    guide = GUIDES[guide_id]
    targets = [row.get('Герой', ''), row.get('Второй герой', '')]

    for target in targets:
        words = target.strip().split()
        if any(
                get_close_matches(word, [guide['name'], guide['surname']], cutoff=0.7)
                for word in words
        ):
            return True
    return False


# =================== Major filtering ===================
def filter_data(
        data: list[dict],
        columns: list[str],
        start_date: date,
        end_date: Optional[date] = None,
        guide_id: Optional[int] = None
) -> list[dict]:
    """
    Универсальная функция для фильтрации экскурсий Славны по дате или конкретному периоду.
    Может фильтровать по гиду, если передан guide_id.
    """

    return [
        {header: info for header, info in row.items() if header in columns and info}
        for row in data
        if (date_value := format_date(row.get('Дата')))
           and start_date <= date_value <= (end_date or start_date)
           and (
                   not guide_id
                   or guide_mentioned_with_typos(row, guide_id)
           )
    ]


def filter_data_from_today(data: list[dict], columns: list[str], guide_id: Optional[int] = None) \
        -> list[dict]:
    """
    Универсальная функция для фильтрации всех экскурсий Славны с сегодняшнего дня.
    Может фильтровать по гиду, если передан guide_id.
    """

    return [
        {header: info for header, info in row.items() if header in columns and info}
        for row in data
        if (date_value := format_date(row.get('Дата')))
           and date_value >= date.today()
           and (
                   not guide_id
                   or guide_mentioned_with_typos(row, guide_id)
           )
    ]


# =================== Tripster for guides handling ===================
def get_tripster_and_slavna_tours(guide: int, slavna_data: list[dict], columns: list[str],
                                  start_date: Optional[date] = None, end_date: Optional[date] = None,
                                  from_today: bool = False) -> list[dict]:
    """
    Получает экскурсии из других доксов и объединяет их с данными Славны на дату или период.

    Args:
        guide (int): ID гида
        slavna_data (list[dict]): Основные данные экскурсий
        columns (list[str]): Колонки для фильтрации (docs Славны)
        start_date (Optional[date]): Начальная дата периода
        end_date (Optional[date]): Конечная дата периода
        from_today (bool): Если True, фильтрует только с сегодняшнего дня.

    Returns:
        list[dict]: Отфильтрованные и объединенные экскурсии
    """
    brief_columns = get_brief_mpcols()

    if guide == feofaniya:
        tripster_data = get_extra_orders('Маркова')
        extra_columns = get_m_columns()
    elif guide == zabava:
        tripster_data = get_extra_orders('Путятина')
        extra_columns = get_p_columns()
    else:
        return []

    if from_today:
        tripster_tours = filter_data_from_today(tripster_data, brief_columns)
        slavna_tours = filter_data_from_today(slavna_data, columns, guide_id=guide)
    else:
        tripster_columns = brief_columns if end_date else extra_columns
        tripster_tours = filter_data(tripster_data, tripster_columns, start_date=start_date, end_date=end_date)
        slavna_tours = filter_data(slavna_data, columns, start_date=start_date, end_date=end_date,
                                   guide_id=guide)
    logger.debug(f"Славна: {len(slavna_tours)} экскурсий, Трипстер: {len(tripster_tours)} экскурсий.")

    return sort_tours(tripster_tours + slavna_tours)


# =================== Condition filtering ===================
def filter_by_date(due_date: Optional[date] = None, guide: Optional[int] = None) -> list[dict] | None:
    """
    Фильтрует данные из google sheet на дату.
    Может фильтровать по гиду, если передан id гида.
    Для двух гидов также добавляет данные на дату из других google sheets.

    Если due_date передан, фильтрует данные за указанную дату.
    В противном случае фильтрует данные за сегодняшнюю дату.

    Args:
        due_date (Optional[date], optional): Дата для фильтрации. Если не указано, используется текущая дата
        guide (Optional[int]): Id гида для фильтрации его экскурсий.

    Returns:
        Optional[List[Dict[str, Any]]]: Фильтрованные данные или None в случае ошибки.
    """
    try:
        data = get_orders()
        tour_date = due_date or date.today()

        if guide:
            columns = get_guides_columns()
            if guide in (feofaniya, zabava):
                # Для Феофании и Забавы
                return get_tripster_and_slavna_tours(guide, data, columns, start_date=tour_date)
            # Для Агафьи
            return filter_data(data, columns, tour_date, guide_id=guide)
        # Для админов
        columns = get_extended_columns()
        return filter_data(data, columns, tour_date)
    except Exception as e:
        logger.error(f"Ошибка при загрузке или фильтрации данных: {e}")
        return None


def filter_by_period(start_date: Optional[date] = None, end_date: Optional[date] = None, guide: Optional[int] = None) \
        -> list[dict] | None:
    """
    Фильтрует данные из google sheet за указанный период.
    Может фильтровать по гиду, если передан id гида.
    Для двух гидов также добавляет данные из других google sheets.

    Если обе даты переданы, фильтрует данные за указанный период.
    В противном случае фильтрует данные с текущей даты до конца списка.

    Args:
        guide (int): Id гида для фильтрации его экскурсий
        start_date (Optional[date], optional): Начальная дата для фильтрации. Если не указано, используется текущая дата
        end_date (Optional[date], optional): Конечная дата для фильтрации. Если не указано, используется конец списка.

    Returns:
        Optional[List[Dict[str, Any]]]: Фильтрованные данные или None в случае ошибки.
    """
    try:
        # Получаем данные из гугл-таблице
        data = get_orders()
        start_date = start_date or date.today()

        if guide:
            # Отбираем нужные колонки (экскурсии от Славны)
            columns = get_brief_columns()
            # Экскурсии на заданный период
            if start_date and end_date:
                if guide in (feofaniya, zabava):
                    return get_tripster_and_slavna_tours(guide, data, columns, start_date, end_date)
                # Для Агафьи
                return filter_data(data, columns, start_date, end_date, guide_id=guide)
                # Фильтрация данных с сегодняшнего дня
            else:
                if guide in (feofaniya, zabava):
                    return get_tripster_and_slavna_tours(guide, data, columns, from_today=True)
                # Для Агафьи
                return filter_data_from_today(data, columns, guide_id=guide)
        # Для админов
        else:
            columns = get_brief_columns()
            # Экскурсии на заданный период
            if start_date and end_date:
                return filter_data(data, columns, start_date, end_date)
            # Фильтрация данных с сегодняшнего дня
            else:
                return filter_data_from_today(data, columns)
    except Exception as e:
        logger.error(f"Ошибка при загрузке или фильтрации данных: {e}")
        return None


# =================== Super Admin ===================
def get_data_for_sa(slavna_tours: list[dict],
                    columns: list[str],
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None,
                    from_today: bool = False) -> list[dict]:
    """ Собирает данные по экскурсиям обоих гидов с личных Трипстеров и все экскурсии Славны"""
    # Сбор данных с личных Трипстеров
    tripster_m = get_extra_orders('Маркова')
    tripster_p = get_extra_orders('Путятина')
    tripster_data = tripster_m + tripster_p

    # Список всех запланированных экскурсий с личных Трипстеров
    if from_today:
        tripster_tours = filter_data_from_today(tripster_data, columns)

    # Список экскурсий на дату или период с личных Трипстеров
    else:
        tripster_tours = filter_data(tripster_data, columns, start_date=start_date, end_date=end_date)

    logger.debug(f"Славна: {len(slavna_tours)} экскурсий, Трипстер: {len(tripster_tours)} экскурсий.")

    return sort_tours(tripster_tours + slavna_tours)


def filter_for_sa_date(due_date: Optional[date] = None) -> list[dict] | None:
    """
    Фильтрует данные из google sheet по дате для суперадмина: объединяет экскурсии от Славны и двух гидов.

    Если due_date передан, фильтрует данные за указанную дату.
    В противном случае фильтрует данные за сегодняшнюю дату.

    Args:
        due_date (Optional[date], optional): Дата для фильтрации. Если не указано, используется текущая дата.

    Returns:
        Optional[List[Dict[str, Any]]]: Фильтрованные данные или None в случае ошибки.
    """

    # Колонки с Трипстеров (extended)
    extra_mcolumns = get_m_columns()
    extra_pcolumns = get_p_columns()
    columns = extra_mcolumns + extra_pcolumns

    tour_date = due_date if due_date else date.today()

    # Экскурсии от Славны
    slavna_tours = filter_by_date(tour_date)

    return get_data_for_sa(slavna_tours, columns, tour_date)


def filter_for_sa_period(start_date: Optional[date] = None, end_date: Optional[date] = None) -> list[dict] | None:
    """
    Фильтрует данные из google sheet за указанный период для суперадмина: объединяет экскурсии от Славны и двух гидов.

    Если обе даты переданы, фильтрует данные за указанный период.
    В противном случае фильтрует данные с текущей даты до конца списка.

    Args:
        start_date (Optional[date], optional): Начальная дата для фильтрации. Если не указано, используется текущая дата
        end_date (Optional[date], optional): Конечная дата для фильтрации. Если не указано, используется конец списка.

    Returns:
        Optional[List[Dict[str, Any]]]: Фильтрованные данные или None в случае ошибки.
    """

    # Колонки с Трипстеров (brief)
    columns = get_brief_mpcols()

    # Экскурсии от Славны
    slavna_tours = filter_by_period(start_date=start_date, end_date=end_date)

    if start_date and end_date:
        return get_data_for_sa(slavna_tours, columns, start_date, end_date)
    return get_data_for_sa(slavna_tours, columns, date.today(), from_today=True)
