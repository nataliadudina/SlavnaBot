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
from config import bot_config
from logging_config import setup_logging

# передача переменных окружения
config = bot_config

# Инициализация бота и диспетчер
bot = Bot(token=config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Основной цикл бота
async def main():
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)

    # Регистрация роутеров
    dp.include_router(date_handlers.router)
    dp.include_router(period_handlers.router)
    dp.include_router(extra_handlers.router)
    dp.include_router(handlers.router)

    # await set_main_menu(bot)
    # commands = await bot.get_my_commands()
    try:
        await dp.start_polling(bot, timeout=60)
    except Exception as e:
        logger.error(f'error: {e}')


async def main_wrapper():
    """Запускаем проверку экскурсий и бота одновременно"""
    setup_scheduler(bot)
    await main()


if __name__ == '__main__':
    try:
        asyncio.run(main_wrapper())
    except KeyboardInterrupt:
        logging.info('Bot is turned down.')
