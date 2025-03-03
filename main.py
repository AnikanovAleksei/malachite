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
from database import requests as rq
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramForbiddenError

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def send_scheduled_message(bot: Bot):
    users = await rq.get_all_users()
    message_text = ("🌸 Весна наступает – цены тают! 🌞 \n\n"
                    "В магазине Malachite.aps пришло время весенних перемен! \n\n"
                    "Мы подготовили акцию, которая растопит зимний холод, ведь наши скидки "
                    "такие же теплые, как первые лучи солнца. \n\n"
                    
                    "💻 Что вас ждет? \n\n"
                    "- Скидки на технику. \n\n"
                    "- Специальные предложения на новые модели гаджетов. \n\n"
                    "- Подарки при покупке! \n\n"
                    
                    "⏳ Когда? \n\n"
                    "Акции будут проводиться раз в неделю и действуют 24 часа! \n\n"
                    "🌿 Поспешите, пока весенние предложения не растаяли вместе со снегом. \n\n"
                    "🔗 Для уточнения цен акций воспользуйтесь индивидуальным запросом! \n\n")

    image_path = '/root/malachite/image/IMG_1553.JPG'  # Укажите путь к вашему изображению

    # Используем InputFile для отправки изображения
    photo = FSInputFile(image_path)

    for user in users:
        if user.telegram_id:
            try:
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

    # Включаем все роутеры в основной диспетчере
    dp.include_router(main_router)
    dp.include_router(order_router)
    dp.include_router(helper_router)
    dp.include_router(manager_router)

    # Проверка на существование задачи перед добавлением
    if not scheduler.get_job("daily_post"):
        # Настройка планировщика для выполнения задачи в 14:00
        scheduler.add_job(send_scheduled_message, 'cron', hour=17, minute=5, args=[bot], id="daily_post")

    # Запуск планировщика
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
