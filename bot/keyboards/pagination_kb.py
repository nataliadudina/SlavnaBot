from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.texts.staff_texts import pagination


# Функция, генерирующая клавиатуру для страниц
def create_pagination_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    # Кнопка "Назад" активна, если страница не первая
    if current_page > 1:
        kb_builder.add(InlineKeyboardButton(
            text=pagination['backward'],
            callback_data=f"page:{current_page - 1}"
        ))

    # Кнопка с номером страницы
    kb_builder.add(InlineKeyboardButton(
        text=f"{current_page}/{total_pages}",
        callback_data="noop"  # Неактивная кнопка
    ))

    # Кнопка "Вперед" активна, если страница не последняя
    if current_page < total_pages:
        kb_builder.add(InlineKeyboardButton(
            text=pagination['forward'],
            callback_data=f"page:{current_page + 1}"
        ))

    return kb_builder.as_markup()
