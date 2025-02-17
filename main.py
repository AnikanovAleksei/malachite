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
    message_text = ("Акция Лавина Малахита! \n\n"
                    "Спешим сообщить: у нас для вас особое предложение на новейшие смартфоны: \n\n"
                    "- 📱 iPhone 16 Pro 256GB всего за 102,000 рублей \n\n"
                    "- 📱 iPhone 16 Pro Max 256GB всего за 110,000 рублей \n\n"
                    "Чтобы воспользоваться акцией, просто напишите в раздел 'Индивидуальный запрос' с текстом "
                    "'Лавина Малахита'. \n\n"
                    "Не упустите шанс стать обладателем одного из лучших устройств года по специальной цене! 💚 \n\n")

    image_path = '/root/malachite/image/IMG_1436.JPG'  # Укажите путь к вашему изображению

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
        scheduler.add_job(send_scheduled_message, 'cron', hour=19, minute=48, args=[bot], id="daily_post")

    # Запуск планировщика
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
