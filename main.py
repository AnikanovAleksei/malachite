from aiogram import Dispatcher, Bot
import asyncio
import os
from dotenv import load_dotenv
from handlers.handlers import router as handlers_router
from handlers.order import router as order_router
from database.models import async_main
import logging


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv('TOKEN_ID'))


async def main():
    await async_main()
    dp = Dispatcher()
    dp.include_router(handlers_router)
    dp.include_router(order_router)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Exit')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
