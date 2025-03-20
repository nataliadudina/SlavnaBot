from aiogram.types import KeyboardButton, WebAppInfo, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts.staff_texts import buttons

# Создаём reply кнопки
tours = KeyboardButton(text='Экскурсии 🗺️')
contacts = KeyboardButton(text='Контакты 📞')

on_date = KeyboardButton(text=buttons['on_date'])
on_period = KeyboardButton(text=buttons['on_period'])
extra = KeyboardButton(text=buttons['extra'])

web_vk_btn = KeyboardButton(
    text='Группа ВКонтакте',
    web_app=WebAppInfo(url='https://vk.com/slavna53')
)

# Создаем объект reply клавиатуры для пользователей
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[[tours, contacts],
              [web_vk_btn]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Создаем объект reply клавиатуры для админов
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[[on_date, on_period],
              [extra]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# Создаем объект reply клавиатуры для гидов
guide_keyboard = ReplyKeyboardMarkup(
    keyboard=[[on_date, on_period]],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# Создаем объекты инлайн-кнопок на дату
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

# Создаем объекты инлайн-кнопок на период
period = InlineKeyboardButton(
    text=buttons['period'],
    callback_data='period_pressed'
)
all_tours = InlineKeyboardButton(
    text=buttons['all_tours'],
    callback_data='all_tours_pressed'
)

# Создаем объекты дополнительных инлайн-кнопок
tripster = InlineKeyboardButton(
    text='Tripster 🧭',
    callback_data='tripster_pressed'
)
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

# Inline кнопки подменю для Трипстера
send_tdy_notes = InlineKeyboardButton(
    text='Уведомления на сегодня',
    callback_data='send_tdy_pressed'
)
send_tmrw_notes = InlineKeyboardButton(
    text='Уведомления на завтра',
    callback_data='send_tmrw_pressed'
)
late_orders = InlineKeyboardButton(
    text='Для поздних заказов',
    callback_data='late_orders_pressed'
)

# Создаем объект инлайн-клавиатуры
date_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[today],
                     [tomorrow],
                     [date]]
)
period_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[period],
                     [all_tours]]
)
extra_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[tripster],
                     [gdocs],
                     [qtickets],
                     [vk_btn]]
)
tripster_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [send_tdy_notes],
        [send_tmrw_notes],
        [late_orders]
    ]
)
