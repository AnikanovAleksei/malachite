from aiogram import Dispatcher, Bot
import asyncio
import os
from dotenv import load_dotenv
from handlers.handlers import router as handlers_router
from handlers.order import router as order_router
from database.models import async_main
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.requests import get_all_users  # Предположим, что у вас есть такая функция
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv('TOKEN_ID'))

# Инициализация планировщика
scheduler = AsyncIOScheduler()


async def send_message_to_all_users(bot_instance: Bot, message_text: str):
    try:
        users = await get_all_users()  # Функция для получения всех пользователей
        semaphore = asyncio.Semaphore(10)  # Ограничение на 10 одновременных запросов

        async def send_message(user):
            async with semaphore:
                await bot_instance.send_message(chat_id=user.telegram_id, text=message_text)

        await asyncio.gather(*(send_message(user) for user in users))
    except Exception as ex:
        logger.error(f"Error sending messages: {ex}")


async def main():
    await async_main()
    dp = Dispatcher()
    dp.include_router(handlers_router)
    dp.include_router(order_router)

    # Пример текста сообщения для рассылки
    message_text = (
        "В честь открытия бота!\n\n🔔 "
        "У нас отличная новость для всех любителей новинок Apple!\n\n🎉 "
        "\"iPhone 16 Pro Max\" всего от 123.000₽!\n\n💥 "
        "Не упустите возможность стать одним из обладателей самого передового смартфона!\n\n📱 "
        "Заказывайте прямо сейчас и наслаждайтесь всеми преимуществами новой модели.\n\n"
        "С уважением, ваша команда технической поддержки!"
    )

    # Начальная рассылка
    await send_message_to_all_users(bot, message_text)

    # Планирование рассылки каждые 24 часа
    scheduler.add_job(send_message_to_all_users, 'interval', minutes=10, args=[bot, message_text])

    # Запуск планировщика
    scheduler.start()

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Exit')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
