import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.bot.db import get_users
from src.bot.filters import is_superadmin, is_admin, is_guide
from src.bot.keyboards import check_btn
from src.googlesheets.tours_filtering import filter_for_sa_date, filter_by_date

logger = logging.getLogger()


async def check_tours(bot):
    """ Checks nearest tours and sends notifications to admins and guides. """
    admins_notif = date.today() + timedelta(days=2)
    guides_notif = date.today() + timedelta(days=1)
    users = get_users()

    for user_id in users:
        try:
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
                continue

            if not tours and not errors:
                continue

            response = (f"🔔 На {day} запланировано экскурсий: {len(tours) + len(errors)}.\n"
                        f"Проверьте расписание.")

            await bot.send_message(chat_id=user_id, text=response, reply_markup=check_btn, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Error while sending notification to user {user_id}: {e}")


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(check_tours, 'cron', hour=11, minute=0, args=[bot])
    scheduler.start()
