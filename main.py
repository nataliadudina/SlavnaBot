import asyncio
import logging
import logging.config

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import bot.handlers
from bot.handlers import handlers, date_handlers, extra_handlers, period_handlers
from bot.scheduler import setup_scheduler
from config import config
from logging_config import setup_logging

bot = Bot(token=config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    bot_info = await bot.get_me()
    logger.info('Starting bot: @%s', bot_info.username)

    # Routers
    dp.include_router(date_handlers.router)
    dp.include_router(period_handlers.router)
    dp.include_router(extra_handlers.router)
    dp.include_router(handlers.router)

    try:
        await dp.start_polling(bot, timeout=60)
    except Exception as e:
        logger.error(f'error: {e}')


async def main_wrapper():
    setup_scheduler(bot)
    await main()


if __name__ == '__main__':
    try:
        logging.info('Bot process started')
        asyncio.run(main_wrapper())
    except KeyboardInterrupt:
        logging.info('Bot is turned down.')
    except Exception:
        logging.exception('Fatal error during bot execution')
