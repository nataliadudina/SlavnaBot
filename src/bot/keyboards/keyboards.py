from aiogram.types import KeyboardButton, WebAppInfo, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.texts.staff_texts import buttons

# =========================
# GUESTS
# =========================
# Make reply buttons
tours = KeyboardButton(text='Экскурсии 🗺️')
contacts = KeyboardButton(text='Контакты 📞')

on_date = KeyboardButton(text=buttons['on_date'])
on_period = KeyboardButton(text=buttons['on_period'])
extra = KeyboardButton(text=buttons['extra'])

web_vk_btn = KeyboardButton(
    text='Группа ВКонтакте',
    web_app=WebAppInfo(url='https://vk.com/slavna53')
)

# Make reply keyboard for users
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[[tours, contacts],
              [web_vk_btn]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# =========================
# ADMINS & GUIDES
# =========================
# Make reply keyboard for admins
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[[on_date, on_period],
              [extra]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# Make reply keyboard for guides
guide_keyboard = ReplyKeyboardMarkup(
    keyboard=[[on_date, on_period]],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# Make inline menu for Date
today = InlineKeyboardButton(
    text=buttons['today'],
    callback_data='today_pressed'
)
tomorrow = InlineKeyboardButton(
    text=buttons['tomorrow'],
    callback_data='tomorrow_pressed'
)
date = InlineKeyboardButton(
    text=buttons['date'],
    callback_data='date_pressed'
)

# Make inline menu for Period
period = InlineKeyboardButton(
    text=buttons['period'],
    callback_data='period_pressed'
)
all_tours = InlineKeyboardButton(
    text=buttons['all_tours'],
    callback_data='all_tours_pressed'
)

# Make inline menu for admins' additional options
# tripster = InlineKeyboardButton(
#     text='Tripster 🧭',
#     callback_data='tripster_pressed'
# )
qtickets = InlineKeyboardButton(
    text='qtickets',
    url='https://qtickets.app/orders'
)
vk_btn = InlineKeyboardButton(
    text='ВКонтакте',
    url='https://vk.com/slavna53'
)
gdocs = InlineKeyboardButton(
    text='Google Doc 🖊',
    callback_data='gdocs_pressed'
)
excursions = InlineKeyboardButton(
    text='🧭 Экскурсии',
    callback_data='excursions_pressed'
)

extra_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[gdocs],
                     [excursions],
                     [qtickets],
                     [vk_btn]]
)

# Inline keyboards (Date & Period)
date_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[today],
                     [tomorrow],
                     [date]]
)
period_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[period],
                     [all_tours]]
)

# Excursions handling

# --- Level 1: Excursions ---
add_tour = InlineKeyboardButton(
    text=buttons['add_tour'],
    callback_data='add_tour_pressed'
)
edit_tour = InlineKeyboardButton(
    text=buttons['edit_tour'],
    callback_data='edit_tour_pressed'
)
delete_tour = InlineKeyboardButton(
    text=buttons['delete_tour'],
    callback_data='delete_tour_pressed'
)
back_to_extra = InlineKeyboardButton(
    text=buttons['back'],
    callback_data='back_to_extra'
)

excursions_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [add_tour],
        [edit_tour],
        [delete_tour],
        [back_to_extra],
    ]
)

# --- Level 2: Add tour type ---
add_on_request = InlineKeyboardButton(
    text=buttons['on_request'],
    callback_data='add_on_request'
)
add_in_group = InlineKeyboardButton(
    text=buttons['in_group'],
    callback_data='add_in_group'
)
back_to_excursions = InlineKeyboardButton(
    text=buttons['back'],
    callback_data='back_to_excursions'
)

add_tour_type = InlineKeyboardMarkup(
    inline_keyboard=[
        [add_on_request],
        [add_in_group],
        [back_to_excursions],
    ]
)

# --- Level 2: Edit tour type ---
edit_on_request = InlineKeyboardButton(
    text=buttons['on_request'],
    callback_data='edit_on_request'
)
edit_in_group = InlineKeyboardButton(
    text=buttons['in_group'],
    callback_data='edit_in_group'
)

edit_tour_type = InlineKeyboardMarkup(
    inline_keyboard=[
        [edit_on_request],
        [edit_in_group],
        [back_to_excursions],
    ]
)

back_to_types = InlineKeyboardButton(
    text=buttons['back'],
    callback_data='back_to_types'
)

back_to_list = InlineKeyboardButton(
    text=buttons['back'],
    callback_data='back_to_list'
)


def edit_tours_list_keyboard(tours: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    keyboard = []

    for tour_id, title in tours:
        keyboard.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f'edit_tour_select:{tour_id}',
            )
        ])

    keyboard.append([back_to_types])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def edit_tour_actions_keyboard(tour_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✏️ Название',
                    callback_data=f'edit_tour_title:{tour_id}',
                )
            ],
            [
                InlineKeyboardButton(
                    text='✏️ Описание',
                    callback_data=f'edit_tour_description:{tour_id}',
                )
            ],
            [back_to_list],
        ]
    )


# --- Level 3: Delete tour type ---
def delete_tour_list(tours: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    keyboard = []

    for tour_id, title in tours:
        keyboard.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f'delete_tour_select:{tour_id}',
            )
        ])

    keyboard.append([back_to_excursions])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def delete_tour_confirm_keyboard(tour_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='🗑 Да, удалить',
                    callback_data=f'delete_tour_confirm:{tour_id}',
                ),
                InlineKeyboardButton(
                    text=buttons['back'],
                    callback_data='delete_tour_cancel',
                )
            ],
        ]
    )


# Check button to see excursions for tomorrow (attached to scheduled notification)
check_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Посмотреть 👀', callback_data='check')]
    ]
)

# ################ TO DELETE #################
# Inline кнопки подменю для Трипстера
# send_tdy_notes = InlineKeyboardButton(
#     text='Уведомления на сегодня',
#     callback_data='send_tdy_pressed'
# )
# send_tmrw_notes = InlineKeyboardButton(
#     text='Уведомления на завтра',
#     callback_data='send_tmrw_pressed'
# )
# late_orders = InlineKeyboardButton(
#     text='Для поздних заказов',
#     callback_data='late_orders_pressed'
# )
#
# tripster_keyboard = InlineKeyboardMarkup(
#     inline_keyboard=[
#         [send_tdy_notes],
#         [send_tmrw_notes],
#         [late_orders]
#     ]
# )
# ####################################
