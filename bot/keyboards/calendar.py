from datetime import datetime

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


async def generate_calendar(
        year: int,
        month: int,
        is_period: bool = False,
        selected_start_date: str = None,
        selected_end_date: str = None
):
    """
    Генерация inline-календаря с подсветкой выбранных дат и диапазона (если is_period=True).
    """
    prefix = "pnavigate_" if is_period else "navigate_"
    builder = InlineKeyboardBuilder()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    # Строка с месяцем и годом
    prev_month = month - 1 if month > 1 else 12
    next_month = month + 1 if month < 12 else 1
    prev_year = year if month > 1 else year - 1
    next_year = year if month < 12 else year + 1

    builder.row(
        InlineKeyboardButton(text="<", callback_data=f"{prefix}{prev_year}_{prev_month}"),
        InlineKeyboardButton(text=f"{MONTH_NAMES[month - 1]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text=">", callback_data=f"{prefix}{next_year}_{next_month}")
    )

    # Строка с днями недели
    builder.row(*[InlineKeyboardButton(text=day, callback_data="ignore") for day in days])

    # Генерация дней месяца
    date = datetime(year, month, 1)
    start_weekday = date.weekday()  # День недели начала месяца (0 - понедельник)
    empty_days = start_weekday  # Количество пустых дней в первой строке

    # Конвертация строковых дат в объекты datetime
    start_date = datetime.strptime(selected_start_date, '%Y-%m-%d').date() if selected_start_date else None
    end_date = datetime.strptime(selected_end_date, '%Y-%m-%d').date() if selected_end_date else None

    # Добавляем пустые кнопки в начале (если месяц не начинается с понедельника)
    week = [InlineKeyboardButton(text=" ", callback_data="ignore") for _ in range(empty_days)]

    for day in range(1, 32):  # До 31 дня
        try:
            current_date = datetime(year, month, day).date()

            # Определяем callback_data для кнопок
            if is_period:
                callback_data = f"period_date_{current_date.strftime('%Y-%m-%d')}"
            else:
                callback_data = f"date_{current_date.strftime('%Y-%m-%d')}"

            # Подсветка выбранных дат
            if current_date == start_date or current_date == end_date:
                text = f"{day}*"  # Подсвечиваем выбранный день
            elif start_date and end_date and start_date < current_date < end_date:
                text = f"({day})"  # Диапазон между начальной и конечной датой
            else:
                text = str(day)

            week.append(InlineKeyboardButton(text=text, callback_data=callback_data))

            # Если неделя заполнена, добавляем строку в клавиатуру
            if len(week) == 7:
                builder.row(*week)
                week = []
        except ValueError:
            break

    # Добавляем оставшиеся дни (если есть)
    if week:
        while len(week) < 7:  # Заполняем оставшиеся кнопки пустыми
            week.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        builder.row(*week)

    return builder.as_markup()
