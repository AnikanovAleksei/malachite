from aiogram import Dispatcher, Bot
import asyncio
import os
from dotenv import load_dotenv
from handlers.handlers import router as handlers_router
from handlers.order import router as order_router
from database.models import async_main
import logging
from database import requests as rq


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

    await rq.send_message_to_all_users(bot, "🎉 Акция «Лавина Малахита» в Malachite Store! 🎉\n\n"
                                            "Только сейчас у вас есть возможность приобрести последние модели\n"
                                            "iPhone по потрясающим ценам!\n\n"
                                            "Ощутите все преимущества современных технологий с Malachite Store.\n\n"
                                            "📱 iPhone 16 Pro Max 256 ГБ всего за 114,890 рублей!\n\n"
                                            "📱 iPhone 16 Pro 256 ГБ всего за 106,890 рублей!\n\n"
                                            "Чтобы воспользоваться этой акцией, просто свяжитесь с нашим менеджером "
                                            "через  индивидуальный запрос с текстом сообщения «Лавина».\n\n"
                                            "Спешите! Количество акционных товаров ограничено. Маленькая "
                                            "'Лавина' может изменить ваш мир! 📲✨\n\n"
                                            "Цены действительны один день")

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Exit')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
