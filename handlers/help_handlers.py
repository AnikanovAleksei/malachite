from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

HELP_COMMAND = """
/start - перезапуск
/menu - каталог
/help - список команд
/contact - связь с менеджером
"""

router = Router()


# Обработка команды /help
@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(text=HELP_COMMAND)
