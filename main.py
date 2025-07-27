import os
import asyncio
from aiogram import Dispatcher, Bot
from dotenv import load_dotenv
from handlers.handlers import router as main_router
from handlers.order import handlers_router as order_router
from handlers.contact import router as manager_router
from handlers.help_handlers import router as helper_router
from database.models import async_main
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from handlers.admin import router as admin_router

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def main():
    load_dotenv()
    await async_main()
    bot = Bot(token=os.getenv('TOKEN_ID'))

    dp = Dispatcher()

    # Включаем все роутеры в основной диспетчере
    dp.include_router(main_router)
    dp.include_router(order_router)
    dp.include_router(helper_router)
    dp.include_router(manager_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
