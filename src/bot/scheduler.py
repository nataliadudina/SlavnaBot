import logging
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..bot.db import get_users
from ..bot.db.db import get_user_email
from ..bot.filters import is_superadmin, is_admin, is_guide
from ..bot.keyboards import check_btn
from ..config import config
from ..googlesheets.tours_filtering import filter_for_sa_date, filter_by_date, GUIDES

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
    debug_data = {}

    for user_id in get_users():
        try:
            result = build_notification(user_id)
            if not result:
                continue

            day, tours, errors = result
            text = build_message(day, tours, errors)

            if tours:
                debug_data[user_id] = len(tours)

            await bot.send_message(chat_id=user_id, text=text, reply_markup=check_btn, parse_mode='HTML')

        except Exception as e:
            logger.error(f'Error while sending notification to user {user_id}: {e}')

    summary = '; '.join(f'{uid}: {t} tours' for uid, t in debug_data.items())
    logger.info(f'Bot notifications summary: {summary}')


async def notify_email():
    """Sends email notifications."""
    debug_data = {}

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

            if tours:
                debug_data[user_id] = len(tours)

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

    guides = [GUIDES.get(uid.get('name'), str(uid)) for uid in debug_data.keys()]
    summary = '; '.join(f'{GUIDES.get(uid.get("name"), uid)}: {t} tours' for uid, t in debug_data.items())
    logger.info(f'Email notifications summary: {summary}')
    logger.error(f'Emails are sent to {", ".join(guides)}')


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(notify_telegram, 'cron', hour=11, minute=0, args=[bot])
    scheduler.add_job(notify_email, 'cron', hour=19, minute=0)
    scheduler.start()
