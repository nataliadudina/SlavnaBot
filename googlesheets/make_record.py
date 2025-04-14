import calendar
from datetime import datetime

from googlesheets.docs_parsing import worksheet

SHEET = worksheet


def parse_record(data: list) -> list:
    """ Готовит данные для записи в google doc"""

    tour_type = {
        1: 'Кремль город держит',
        2: 'По Детинцу да по Пискупле',
        3: 'К хозяйке славенского конца',
        4: 'Ай-да на Славню',
        5: 'Заморские купцы',
        6: 'История в двух голосах',
        7: 'Иное'
    }
    # Обязательные данные
    tour_date = data[0]
    tour_time = data[1]

    if data[2].isdigit() and int(data[2]) in range(1, 8):
        tour = tour_type[int(data[2])]
    else:
        tour = data[2].title()

    client_data = [el.title().strip() for el in data[3].split(',', maxsplit=1)]
    client, contacts = client_data if len(client_data) == 2 else (client_data[0], '')

    # Дополнительные данные
    guides = [g.title().strip() for g in data[4].split(',', maxsplit=1)]
    guide1, guide2 = guides if len(guides) == 2 else (guides[0], '')

    price = data[5]

    guests = [g.strip() for g in data[6].split(',', maxsplit=1)]
    count, cat = guests if len(guests) == 2 else (guests[0], '')

    place = [p.strip() for p in data[7].split(',', maxsplit=1)]
    start, end = place if len(place) == 2 else (place[0], '')

    record_data = [tour_date, tour_time, tour, guide1, guide2, client, price, count, cat, contacts, start, end]
    return record_data


def find_insert_index(data, new_datetime) -> int:
    """
    Определяет индекс, куда вставить новую запись, чтобы сохранить сортировку по дате и времени.
    """
    for i, row in enumerate(data):
        try:
            row_datetime = datetime.strptime(row[0] + ' ' + row[1], '%d.%m.%Y %H:%M')

            if new_datetime < row_datetime:
                return i + 1
        except (ValueError, IndexError):
            if i + 1 < len(data):

                try:
                    next_row = data[i + 1]
                    next_datetime = datetime.strptime(next_row[0] + ' ' + next_row[1], '%d.%m.%Y %H:%M')
                    if (new_datetime.year, new_datetime.month) < (next_datetime.year, next_datetime.month):
                        return i + 1
                except (ValueError, IndexError):
                    continue

    return len(data) + 1


def add_record(record_data):
    """ Вставляет новую запись в нужное место в Google Sheets."""
    data = SHEET.get_all_values()

    # Находим нужную строку
    new_datetime = datetime.strptime(record_data[0] + ' ' + record_data[1], '%d.%m.%Y %H:%M')
    insert_index = find_insert_index(data, new_datetime)

    new_record = parse_record(record_data)
    SHEET.insert_row(new_record, insert_index)

    # Выделяем строку цветом
    SHEET.format(f"A{insert_index}:L{insert_index}", {
        "backgroundColor": {
            "red": 1.0, "green": 0.95, "blue": 0.8
        }
    })
