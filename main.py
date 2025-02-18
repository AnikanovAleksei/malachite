from aiogram import Dispatcher, Bot
import asyncio
import os
from dotenv import load_dotenv
from handlers.handlers import router as handlers_router
from database.models import async_main
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import requests as rq
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramForbiddenError

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def send_scheduled_message(bot: Bot):
    users = await rq.get_all_users()
    message_text = ("📢 Магазин техники Malachite APS! \n\n"

                    "🔹 Быстрая доставка \n\n"
                    "Мы ценим ваше время, поэтому гарантируем быструю доставку всех заказов. \n\n"
                    "Вы получите свою технику в кратчайшие сроки! \n\n"

                    "🔹 Отличные цены \n\n"
                    "Наш магазин предлагает лучшие цены на рынке. Мы всегда стремимся"
                    "к тому, чтобы сделать покупки выгодными для вас. \n\n"

                    "🔹 Индивидуальный запрос \n\n"
                    "Не нашли то, что искали в нашем каталоге? Не проблема! Воспользуйтесь функцией"
                    "индивидуального запроса, и мы найдем именно то, что вам нужно. \n\n"
        
                    "Malachite APS — ваш надежный партнер в мире техники! \n\n"
                    "Оставайтесь с нами, следите за новинками и спец предложениями. \n\n")

    image_path = '/root/malachite/image/IMG_1438.JPG'  # Укажите путь к вашему изображению

    # Используем InputFile для отправки изображения
    photo = FSInputFile(image_path)

    for user in users:
        if user.telegram_id:
            try:
                # Отправка фото с подписью
                await bot.send_photo(chat_id=user.telegram_id, photo=photo, caption=message_text)
            except TelegramForbiddenError:
                print(f"Bot was blocked by the user {user.telegram_id}")
            except Exception as e:
                print(f"Failed to send message to user {user.telegram_id}: {e}")


async def main():
    load_dotenv()
    await async_main()
    bot = Bot(token=os.getenv('TOKEN_ID'))

    dp = Dispatcher()
    dp.include_router(handlers_router)

    # Проверка на существование задачи перед добавлением
    if not scheduler.get_job("daily_post"):
        # Настройка планировщика для выполнения задачи в 14:00
        scheduler.add_job(send_scheduled_message, 'cron', hour=13, minute=35, args=[bot], id="daily_post")

    # Запуск планировщика
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
