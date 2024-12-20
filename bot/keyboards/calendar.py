from datetime import datetime

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


async def generate_calendar(year: int, month: int, is_period: bool = False):
    builder = InlineKeyboardBuilder()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    # Строка с месяцем и годом
    prev_month = month - 1 if month > 1 else 12
    next_month = month + 1 if month < 12 else 1
    prev_year = year if month > 1 else year - 1
    next_year = year if month < 12 else year + 1

    builder.row(
        InlineKeyboardButton(text="<", callback_data=f"navigate_{prev_year}_{prev_month}"),
        InlineKeyboardButton(text=f"{MONTH_NAMES[month - 1]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text=">", callback_data=f"navigate_{next_year}_{next_month}")
    )

    # Строка с днями недели
    builder.row(*[InlineKeyboardButton(text=day, callback_data="ignore") for day in days])

    # Генерация дней месяца
    date = datetime(year, month, 1)
    start_weekday = date.weekday()  # День недели начала месяца (0 - понедельник)
    empty_days = start_weekday  # Количество пустых дней в первой строке

    # Добавляем пустые кнопки в начале (если месяц не начинается с понедельника)
    week = [InlineKeyboardButton(text=" ", callback_data="ignore") for _ in range(empty_days)]

    for day in range(1, 32):  # До 31 дня
        try:
            date = datetime(year, month, day)
            if is_period:
                callback_data = f"period_date_{date.strftime('%Y-%m-%d')}"
            else:
                callback_data = f"date_{date.strftime('%Y-%m-%d')}"

            week.append(InlineKeyboardButton(text=str(day), callback_data=callback_data))
            if len(week) == 7:  # Если неделя заполнена
                builder.row(*week)  # Добавляем строку в клавиатуру
                week = []
        except ValueError:
            break

    # Добавляем оставшиеся дни (если есть)
    if week:
        while len(week) < 7:  # Заполняем оставшиеся кнопки пустыми
            week.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        builder.row(*week)

    return builder.as_markup()
