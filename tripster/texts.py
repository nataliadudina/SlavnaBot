from datetime import date, datetime


def form_message(tour: str, name: str, str_date: str, time: datetime, amount: int) -> str:
    tour_date = datetime.strptime(str_date, '%d.%m.%Y')
    when = ('Завтра', 'Сегодня')[tour_date.date() == date.today()]

    tradeside = f'Здравствуйте, {name.title()}!\n' \
                f'Благодарим Вас за бронирование экскурсии {tour}. ' \
                f'{when} в {time} будем ждать Вас у входа в «Амакс отель Россия».\n' \
                f'Точка на карте:\n' \
                f'наб. Александра Невского, 19/1, Торговая сторона\n' \
                f'https://yandex.ru/maps/org/amaks_otel_rossiya/1146845793\n\n' \
                f'Продолжительность экскурсии - 1,5 часа.\n' \
                f'Оплатить экскурсию Вы сможете по ее завершении наличными ' \
                'или по ссылке: https://yookassa.ru/my/i/aHD4glgDOnXK/l\n' \
                f'Сумма к доплате: {amount} рублей.\n\n' \
                f'По всем вопросам - обращайтесь!'
# 'https://yookassa.ru/my/i/aGFvmNKOrNdm/l'
    kremlin = f'Здравствуйте, {name.title()}!\n' \
              f'Благодарим Вас за бронирование экскурсии {tour}. ' \
              f'{when} в {time} будем ждать Вас у входа в Кремль со стороны Софийской площади.\n\n' \
              f'Точка на карте:\n' \
              f'Схема Новгородского Кремля, Софийская площадь\n'\
              f'https://yandex.ru/maps/24/veliky-novgorod/?ll=31.273973%2C58.522129&mode=poi&poi%5Bpoint%5D=31.272882%2C58.522375&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D61143759664&z=17.05\n\n' \
              f'Продолжительность экскурсии - 1,5 часа.\n' \
              f'Оплатить экскурсию Вы сможете по ее завершении наличными ' \
              f'или по ссылке: https://yookassa.ru/my/i/aGFwtBYZ_AdN/l \n\n' \
              f'Сумма к доплате: {amount} рублей.\n\n' \
              f'По всем вопросам - обращайтесь!'

    if 'Детинцу' in tour:
        return kremlin
    return tradeside
