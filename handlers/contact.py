from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards import keyboards as kb

router = Router()


# Обработка команды /contact
@router.message(Command('contact'))
async def start_command(message: Message):
    await message.answer(
        "Для связи с менеджером нажмите на кнопку ниже:",
        reply_markup=kb.main_inline
    )


# Обработка связи с менеджером
@router.callback_query(F.data == 'connect')
async def cmd_connect(callback: CallbackQuery):
    await callback.answer('Связь установлена', show_alert=True)
    url_manager = 'https://t.me/malachite_aps'
    await callback.message.answer(f"Вот ссылка на профиль: {url_manager}")


# Обработка связи с менеджером
@router.message(F.text == 'Связь с менеджером')
async def send_contact(message: Message):
    url_manager = 'https://t.me/malachite_aps'
    await message.answer(f"Вот ссылка на профиль: {url_manager}")
