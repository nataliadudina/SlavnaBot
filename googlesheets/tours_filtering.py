import logging
import re
from datetime import datetime, date
from typing import Optional

from environs import Env

from googlesheets.docs_parsing import get_extended_columns, get_brief_columns, get_guides_columns, get_orders
from googlesheets.mydocs_parsing import get_m_columns, get_p_columns, get_extra_orders

logger = logging.getLogger(__name__)

env = Env()
env.read_env('.env')
# Guides' ids
zabava = int(env('ZABAVA'))
agafya = int(env('AGAFYA'))
feofaniya = int(env('FEOFANIYA'))

# Telegram ids гидов
GUIDES = {
    zabava: 'Забава',
    agafya: 'Агафья',
    feofaniya: 'Феофания'
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


def filter_data(data: list[dict], columns: list[str], start_date: date, end_date: Optional[date] = None) -> list[dict]:
    """
    Универсальная функция для фильтрации данных по дате или периоду.
    """
    return [
        {header: info for header, info in row.items() if header in columns and info}
        for row in data
        if (date_value := format_date(row.get('Дата')))
           and start_date <= date_value <= (end_date or start_date)
    ]


def filter_guide_data(data: list[dict], columns: list[str], pattern: re.Pattern,
                      start_date: date, end_date: Optional[date] = None) -> list[dict]:
    """
    Универсальная функция для фильтрации экскурсий по гиду.
    """
    return [
        {header: info for header, info in row.items() if header in columns and info}
        for row in data
        if (date_value := format_date(row.get('Дата')))
           and start_date <= date_value <= (end_date or start_date)
           and (pattern.search(row.get('Герой', '').strip()) or pattern.search(row.get('Второй герой', '').strip()))
    ]


def sort_tours(data: list[dict]) -> list[dict]:
    """
    Сортирует данные экскурсий по дате и времени.
    """
    return sorted(
        data,
        key=lambda k: (
            format_date(k['Дата']),
            datetime.strptime(k['Время'], '%H:%M')
        )
    )


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
        data = get_orders()
        columns = get_extended_columns()

        filtered_data = filter_data(data, columns, tour_date)
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
        data = get_orders()
        columns = get_brief_columns()

        # Фильтрация данных на период
        if start_date and end_date:
            filtered_data = filter_data(data, columns, start_date=start_date, end_date=end_date)

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
    Для двух гидов также добавляет данные на дату из других google sheets.

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
        data = get_orders()
        columns = get_guides_columns()

        # Дата для фильтрации
        tour_date = due_date if due_date else date.today()
        # Паттерн для фильтрации экскурсий по гиду
        guide_pattern = GUIDE_PATTERNS.get(guide)

        if guide in (feofaniya, zabava):
            if guide == feofaniya:
                tripster_data = get_extra_orders('Маркова')
                extra_columns = get_m_columns()
            elif guide == zabava:
                tripster_data = get_extra_orders('Путятина')
                extra_columns = get_p_columns()
            # Фильтрация экскурсий с трипстера на дату
            tripster_tours = filter_data(tripster_data, extra_columns, tour_date)
            slavna_tours = filter_guide_data(data, columns, guide_pattern, tour_date)
            logger.debug(f"Славна: {len(slavna_tours)} экскурсий, Трипстер: {len(tripster_tours)} экскурсий.")

            # Объединение списков
            filtered_data = sort_tours(tripster_tours + slavna_tours)
        # Для Агафьи
        else:
            # Фильтрация данных на дату
            filtered_data = filter_guide_data(data, columns, guide_pattern, tour_date)
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
    Для двух гидов также добавляет данные из других google sheets.

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
        # Получаем данные из гугл-таблице и отбираем нужные колонки (экскурсии от Славны)
        data = get_orders()
        columns = get_brief_columns()

        # Паттерн для фильтрации экскурсий по гиду
        guide_pattern = GUIDE_PATTERNS.get(guide)

        # Фильтрация данных на период
        if start_date and end_date:
            if guide in (feofaniya, zabava):
                if guide == feofaniya:
                    tripster_data = get_extra_orders('Маркова')
                    extra_columns = get_m_columns()
                elif guide == zabava:
                    tripster_data = get_extra_orders('Путятина')
                    extra_columns = get_p_columns()

                # Фильтрация экскурсий с Трипстера
                tripster_tours = filter_data(tripster_data, extra_columns, start_date=start_date, end_date=end_date)
                # Фильтрация экскурсий Славны
                slavna_tours = filter_guide_data(data, columns, guide_pattern, start_date=start_date, end_date=end_date)

                filtered_data = sort_tours(tripster_tours + slavna_tours)
            # Для Агафьи
            else:
                filtered_data = filter_guide_data(data, columns, guide_pattern, start_date=start_date,
                                                  end_date=end_date)

        # Фильтрация данных с сегодняшнего дня
        else:
            if guide in (feofaniya, zabava):
                if guide == feofaniya:
                    tripster_data = get_extra_orders('Маркова')
                    extra_columns = get_m_columns()
                elif guide == zabava:
                    tripster_data = get_extra_orders('Путятина')
                    extra_columns = get_p_columns()
                # Фильтрация экскурсий с Трипстера
                tripster_tours = [
                    {header: info for header, info in row.items() if header in extra_columns and info}
                    for row in tripster_data
                    if (date_value := format_date(row.get('Дата'))) and date_value >= date.today()
                ]
                # Фильтрация экскурсий Славны
                slavna_tours = [
                    {header: info for header, info in row.items() if header in columns and info}
                    for row in data
                    if (date_value := format_date(row.get('Дата'))) and date_value >= date.today() and (
                            guide_pattern.search(row.get('Герой').strip()) or guide_pattern.search(
                        row.get('Второй герой').strip()))
                ]

                filtered_data = sort_tours(tripster_tours + slavna_tours)
            # Для Агафьи
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
    # Дата для фильтрации
    tour_date = due_date if due_date else date.today()

    # Экскурсии от Славны
    slavna_tours = filter_by_date(tour_date)

    # Экскурсии с Трипстера гидов
    tripster_m = get_extra_orders('Маркова')
    extra_mcolumns = get_m_columns()

    tripster_p = get_extra_orders('Путятина')
    extra_pcolumns = get_p_columns()

    # Фильтрация экскурсий с трипстера на дату
    tripster_data = tripster_m + tripster_p
    columns = extra_mcolumns + extra_pcolumns
    tripster_tours = filter_data(tripster_data, columns, start_date=tour_date)

    # Объединение и сортировка списков
    filtered_data = sort_tours(tripster_tours + slavna_tours)
    return filtered_data


def filter_for_sa_period(start_date: Optional[date] = None,
                         end_date: Optional[date] = None
                         ) -> list[dict] | None:
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
    # Экскурсии с Трипстера гидов
    tripster_m = get_extra_orders('Маркова')
    extra_mcolumns = get_m_columns()

    tripster_p = get_extra_orders('Путятина')
    extra_pcolumns = get_p_columns()

    tripster_data = tripster_m + tripster_p
    columns = extra_mcolumns + extra_pcolumns

    # Фильтрация данных на период
    if start_date and end_date:
        # Экскурсии с Трипстера
        tripster_tours = filter_data(tripster_data, columns, start_date=start_date, end_date=end_date)

    # Фильтрация данных с сегодняшнего дня
    else:
        # Экскурсии с Трипстера
        tripster_tours = [
            {header: info for header, info in row.items() if header in columns and info}
            for row in tripster_data
            if (date_value := format_date(row.get('Дата'))) and date_value >= date.today()
        ]

    # Экскурсии от Славны
    slavna_tours = filter_by_period(start_date=start_date, end_date=end_date)

    # Объединение и сортировка списков
    filtered_data = sort_tours(tripster_tours + slavna_tours)
    return filtered_data
