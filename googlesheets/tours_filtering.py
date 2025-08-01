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
    """ Date formation """
    try:
        pattern = '%d.%m.%Y'
        return datetime.strptime(str_date, pattern).date()
    except (ValueError, TypeError):
        pass


def sort_tours(data: list[dict]) -> tuple[list[dict], list[str]]:
    """Sorts excursion data by date and time. Skips rows with invalid time and returns them separately."""
    valid_rows = []
    invalid_rows = []

    for row in data:
        try:
            date_obj = format_date(row['Дата'])
            time_str = row.get('Время').strip()
            # Handle period in Time column
            time_start = time_str.split('-')[0].strip()
            if len(time_start.split(':')) == 3:
                time_start = ':'.join(time_start.split(':')[:2])

            time_obj = datetime.strptime(time_start, '%H:%M')
            valid_rows.append((date_obj, time_obj, row))

        except Exception:
            invalid_rows.append(' - '.join([row['Дата'], row['Программа']]))

    # Sort by date and time
    sorted_valid = [item[2] for item in sorted(valid_rows, key=lambda x: (x[0], x[1]))]
    return sorted_valid, invalid_rows


def guide_mentioned_with_typos(row: dict, guide_id: int) -> bool:
    """
    Checks if the guide is mentioned in the row (in the 'Герой' and 'Второй герой' fields),
    taking into account possible typos.
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
    Universal function for filtering Slavna excursions by date or specific period.
    Can filter by guide if guide_id is passed.
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
    Universal function for filtering all Slavna excursions from today.
    Can filter by guide if guide_id is passed.
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
                                  from_today: bool = False) -> tuple[list[dict], list[str]]:
    """
    Receives excursions from other docs and combines them with Slavna's data for a date or period.

    Args:
        guide (int): guide ID
        slavna_data (list[dict]): Main tour data
        columns (list[str]): Columns for filtering (Slavna's docs)
        start_date (Optional[date]): Start date of the period
        end_date (Optional[date]): End date of the period
        from_today (bool): If True, filter from today.

    Returns:
        tuple[list[dict], list[str]]: Filtered and combined excursions data and errors in Time column if any
    """
    brief_columns = get_brief_mpcols()

    if guide == feofaniya:
        tripster_data = get_extra_orders('Маркова')
        extra_columns = get_m_columns()
    elif guide == zabava:
        tripster_data = get_extra_orders('Путятина')
        extra_columns = get_p_columns()
    else:
        return [], []

    if from_today:
        tripster_tours = filter_data_from_today(tripster_data, brief_columns)
        slavna_tours = filter_data_from_today(slavna_data, columns, guide_id=guide)
    else:
        tripster_columns = brief_columns if end_date else extra_columns
        tripster_tours = filter_data(tripster_data, tripster_columns, start_date=start_date, end_date=end_date)
        slavna_tours = filter_data(slavna_data, columns, start_date=start_date, end_date=end_date,
                                   guide_id=guide)
    logger.debug(f"Славна: {len(slavna_tours)} экскурсий, Трипстер: {len(tripster_tours)} экскурсий.")

    tours, errors = sort_tours(tripster_tours + slavna_tours)
    return tours, errors


# =================== Condition filtering ===================
def filter_by_date(due_date: Optional[date] = None, guide: Optional[int] = None) -> tuple[list[dict], list[str]]:
    """
    Filters data from Google Sheet by date.
    Can filter by guide if guide ID is provided.
    For two guides, also adds data for the date from other Google Sheets.

    If due_date is provided, filters data for the specified date.
    Otherwise, filters data for today's date.

    Args:
       due_date (Optional[date], optional): Date for filtering. If not specified, current date is used
       guide (Optional[int]): Guide ID for filtering their tours.

    Returns:
       tuple[list[dict], list[str]]: Filtered data and errors in Time column.
    """
    try:
        data = get_orders()
        tour_date = due_date or date.today()

        if guide:
            columns = get_guides_columns()
            if guide in (feofaniya, zabava):
                # For Феофания & Забава
                tours, errors = get_tripster_and_slavna_tours(guide, data, columns, start_date=tour_date)
                return tours, errors
            # For other guids
            filtered_data = filter_data(data, columns, tour_date, guide_id=guide)
            tours, errors = sort_tours(filtered_data)
            return tours, errors
        # For admins
        columns = get_extended_columns()
        filtered_data = filter_data(data, columns, tour_date)
        tours, errors = sort_tours(filtered_data)
        return tours, errors
    except Exception as e:
        logger.error(f"Ошибка при загрузке или фильтрации данных: {e}")
        return [], []


def filter_by_period(start_date: Optional[date] = None, end_date: Optional[date] = None, guide: Optional[int] = None) \
        -> tuple[list[dict], list[str]]:
    """
    Filters data from Google Sheet for a specified period.
    Can filter by guide if guide ID is provided.
    For two guides, also adds data from other Google Sheets.

    If both dates are provided, filters data for the specified period.
    Otherwise, filters data from the current date to the end of the list.

    Args:
       guide (int): Guide ID for filtering their tours
       start_date (Optional[date], optional): Start date for filtering. If not specified, current date is used
       end_date (Optional[date], optional): End date for filtering. If not specified, end of list is used.

    Returns:
       tuple[list[dict], list[str]]: Filtered data and errors in Time column.
    """
    try:
        # Getting data from a Google sheet
        data = get_orders()
        start_date = start_date or date.today()

        if guide:
            # Selecting the necessary columns (excursions from Slavna)
            columns = get_brief_columns()
            # Excursions for a specified period
            if start_date and end_date:
                if guide in (feofaniya, zabava):
                    tours, errors = get_tripster_and_slavna_tours(guide, data, columns, start_date, end_date)
                    return tours, errors
                # For other guids
                filtered_data = filter_data(data, columns, start_date, end_date, guide_id=guide)
                tours, errors = sort_tours(filtered_data)
                return tours, errors
            else:
                # Filtering data from today
                if guide in (feofaniya, zabava):
                    tours, errors = get_tripster_and_slavna_tours(guide, data, columns, from_today=True)
                    return tours, errors
                # For other guids
                filtered_data = filter_data_from_today(data, columns, guide_id=guide)
                tours, errors = sort_tours(filtered_data)
                return tours, errors
        # For admins
        else:
            columns = get_brief_columns()
            # Excursions for a specified period
            if start_date and end_date:
                filtered_data = filter_data(data, columns, start_date, end_date)
                tours, errors = sort_tours(filtered_data)
                return tours, errors
            else:
                # Filtering data from today
                filtered_data = filter_data_from_today(data, columns)
                tours, errors = sort_tours(filtered_data)
                return tours, errors
    except Exception as e:
        logger.error(f"Ошибка при загрузке или фильтрации данных: {e}")
        return [], []


# =================== Super Admin ===================
def get_data_for_sa(slavna_tours: list[dict],
                    columns: list[str],
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None,
                    from_today: bool = False) -> tuple[list[dict], list[str]]:
    """ Collects tour data from both guides' personal Tripsters and all of Slava's tours"""
    # Collect data from personal Tripsters
    tripster_m = get_extra_orders('Маркова')
    tripster_p = get_extra_orders('Путятина')
    tripster_data = tripster_m + tripster_p

    # List of all excursions from personal Tripsters
    if from_today:
        tripster_tours = filter_data_from_today(tripster_data, columns)

    # List of excursions for a date or a specified period from personal Tripsters
    else:
        tripster_tours = filter_data(tripster_data, columns, start_date=start_date, end_date=end_date)

    logger.debug(f"Славна: {len(slavna_tours)} экскурсий, Трипстер: {len(tripster_tours)} экскурсий.")
    tours, errors = sort_tours(tripster_tours + slavna_tours)
    return tours, errors


def filter_for_sa_date(due_date: Optional[date] = None) -> tuple[list[dict], list[str]]:
    """
    Filters data from Google Sheet by date for superadmin: combines tours from Slava and two guides.

    If due_date is provided, filters data for the specified date.
    Otherwise, filters data for today's date.

    Args:
       due_date (Optional[date], optional): Date for filtering. If not specified, current date is used.

    Returns:
       Tuple[List[Dict[str, Any]], List[str]]: Filtered data and list of errors if any.
    """

    # Columns from personal Tripsters (extended)
    extra_mcolumns = get_m_columns()
    extra_pcolumns = get_p_columns()
    columns = extra_mcolumns + extra_pcolumns

    tour_date = due_date if due_date else date.today()

    # Excursions from Slavna
    slavna_tours, _ = filter_by_date(tour_date)

    all_tours, errors = get_data_for_sa(slavna_tours, columns, tour_date)

    return all_tours, errors


def filter_for_sa_period(start_date: Optional[date] = None, end_date: Optional[date] = None) \
        -> tuple[list[dict], list[str]]:
    """
    Filters data from Google Sheet for a specified period for superadmin: combines tours from Slava and two guides.

    If both dates are provided, filters data for the specified period.
    Otherwise, filters data from the current date to the end of the list.

    Args:
       start_date (Optional[date], optional): Start date for filtering. If not specified, current date is used
       end_date (Optional[date], optional): End date for filtering. If not specified, end of list is used.

    Returns:
       List[Dict[str, Any]]: Filtered data.
    """

    # Columns from personal Tripsters (brief)
    columns = get_brief_mpcols()

    # Excursions from Slavna
    slavna_tours, _ = filter_by_period(start_date=start_date, end_date=end_date)

    if start_date and end_date:
        tours, errors = get_data_for_sa(slavna_tours, columns, start_date, end_date)
        return tours, errors
    tours, errors = get_data_for_sa(slavna_tours, columns, date.today(), from_today=True)
    return tours, errors
