import asyncio
import logging
import logging.config

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import bot.handlers
from bot.handlers import handlers, date_handlers, extra_handlers, period_handlers

from config import bot_config
from logging_config import setup_logging

# передача переменных окружения
config = bot_config

# Инициализация бота и диспетчер
bot = Bot(token=config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
# storage = MemoryStorage()
# dp = Dispatcher(storage=storage)
# registry = DialogRegistry(dp)

# Регистрация диалога
# registry.register(dialog)

# Настройка middleware
# setup_middleware(dp)

# Настройка фильтров
# setup_filters(dp)


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
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f'error: {e}')


if __name__ == '__main__':
    asyncio.run(main())
