from aiogram import Dispatcher, Bot
import asyncio
import os
from dotenv import load_dotenv
from handlers.handlers import router as handlers_router
from handlers.order import router as order_router
from database.models import async_main
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.requests import send_message_to_all_users

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv('TOKEN_ID'))

# Инициализация планировщика
scheduler = AsyncIOScheduler()


async def main():
    await async_main()
    dp = Dispatcher()
    dp.include_router(handlers_router)
    dp.include_router(order_router)

    # Пример текста сообщения для рассылки
    message_text = "Привет! Это рассылка для всех пользователей."

    await send_message_to_all_users(bot, message_text)

    # Планирование рассылки каждые 24 часа
    scheduler.add_job(send_message_to_all_users, 'interval', hours=24, args=[bot, message_text])

    # Запуск планировщика
    scheduler.start()

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
