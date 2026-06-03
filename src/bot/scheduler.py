import logging
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.bot.db import get_users
from src.bot.db.db import get_user_email
from src.bot.filters import is_superadmin, is_admin, is_guide
from src.bot.keyboards import check_btn
from src.config import config
from src.googlesheets.tours_filtering import filter_for_sa_date, filter_by_date

logger = logging.getLogger()


def build_notification(user_id: int | str) -> tuple[str, list[dict], list[str]] | None:
    """Returns (day, tours, errors) or None if user has no role or no tours."""
    admins_notif = date.today() + timedelta(days=2)
    guides_notif = date.today() + timedelta(days=1)

    if is_superadmin(user_id):
        tours, errors = filter_for_sa_date(guides_notif)
        day = 'завтра'
    elif is_admin(user_id):
        tours, errors = filter_by_date(admins_notif)
        day = 'послезавтра'
    elif is_guide(user_id):
        tours, errors = filter_by_date(guides_notif, guide=user_id)
        day = 'завтра'
    else:
        return None

    if not tours and not errors:
        return None

    return day, tours, errors


def build_message(day: str, tours: list[dict], errors: list[str], extended: bool = False) -> str:
    text = (f'🔔 На {day} запланировано экскурсий: {len(tours) + len(errors)}. \n'
            f'Проверьте расписание.')

    if extended:
        def format_tour(tour: dict) -> str:
            return '<br>'.join(f'<b>{header}</b>: {info}' for header, info in tour.items())

        if tours:
            tours_text = '<br><hr><br>'.join(format_tour(tour) for tour in tours)
            text += f'<br><br>{tours_text}'

        if errors:
            text += '<br>'.join(er for er in errors)

    return text


async def notify_telegram(bot):
    for user_id in get_users():
        try:
            result = build_notification(user_id)
            if not result:
                continue

            day, tours, errors = result
            text = build_message(day, tours, errors)

            await bot.send_message(chat_id=user_id, text=text, reply_markup=check_btn, parse_mode='HTML')

        except Exception as e:
            logger.error(f'Error while sending notification to user {user_id}: {e}')


async def notify_email():
    """Sends email notifications."""
    for user_id in get_users():
        try:
            result = build_notification(user_id)
            if not result:
                continue

            day, tours, errors = result
            text = build_message(day, tours, errors, extended=True)
            email = await get_user_email(user_id)

            if not email:
                continue

            message = MIMEMultipart()
            message['From'] = config.email_username
            message['To'] = email
            message['Subject'] = 'Программы на завтра'

            message.attach(MIMEText(text, 'html'))

            await aiosmtplib.send(
                message,
                hostname=config.hostname,
                port=config.port,
                username=config.email_username,
                password=config.email_password,
                use_tls=config.use_tls
            )

        except Exception as e:
            logger.error(f'Error while sending email to {user_id}: {e}')


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(notify_telegram, 'cron', hour=11, minute=0, args=[bot])
    scheduler.add_job(notify_email, 'cron', hour=22, minute=30)
    scheduler.start()
