from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from keyboards import keyboards as kb
from database import requests as rq
from aiogram import Bot

import re

from keyboards.keyboards import get_number, main_keyboard
from database.models import async_session, Order
from database.requests import notify_admins
from filters.config import (IPAD_CATEGORY_ID, MACBOOK_CATEGORY_ID)
from state.register import OrderState

order_router = Router()


@order_router.message(F.text == 'Оформить заказ')
async def order_delivery(message: Message, state: FSMContext):
    user_id = message.from_user.id
    cart_items = await rq.get_basket_items(user_id)

    if not cart_items:
        await message.answer('Добавьте товар, чтобы оформить заказ')
        return

    await message.answer('Внимание! При оформлении заказа Вы даете согласие на обработку персональных данных \n'
                         'Пожалуйста, введите Ваше ФИО:', reply_markup=kb.get_cancel_keyboard())
    await state.set_state(OrderState.waiting_for_name)


@order_router.message(OrderState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await cancel_order(message, state)
        return

    name = message.text
    await state.update_data(name=name)
    await message.answer('Пожалуйста, введите Ваш адрес доставки: \n', reply_markup=ReplyKeyboardRemove())
    await state.set_state(OrderState.waiting_for_address)


@order_router.message(OrderState.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    address = message.text
    await state.update_data(address=address)
    await message.answer(
        f'🎯Мы почти у цели.🎯 \n📱Укажите Ваш номер телефона:📱 \n'
        f'Пример номера телефона: +7 xxx xxx xx xx',
        reply_markup=get_number
    )
    await state.set_state(OrderState.waiting_for_phone)


@order_router.message(OrderState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.content_type == 'contact':
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text

    if re.match(r'^\+?\d{11}$', phone_number):
        await state.update_data(phone=phone_number)
        await message.answer('Пожалуйста, введите Ваш email:', reply_markup=ReplyKeyboardRemove())
        await state.set_state(OrderState.waiting_for_email)
    else:
        await message.answer('Номер указан в неправильном формате. Пример номера телефона: +7 xxx xxx xx xx')


@order_router.message(OrderState.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    email = message.text
    if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        await state.update_data(email=email)
        await message.answer('Пожалуйста, введите желаемую дату и время доставки:', reply_markup=ReplyKeyboardRemove())
        await state.set_state(OrderState.waiting_for_delivery_datetime)
    else:
        await message.answer('Некорректный формат email. Пожалуйста, введите email еще раз:')


@order_router.message(OrderState.waiting_for_delivery_datetime)
async def process_delivery_datetime(message: Message, state: FSMContext, bot: Bot):
    delivery_datetime = message.text
    await state.update_data(delivery_datetime=delivery_datetime)
    user_data = await state.get_data()
    await save_order_to_db(message.from_user.id, user_data)

    # Получаем товары из корзины пользователя
    basket_items = await rq.get_basket_items(message.from_user.id)

    # Формируем сообщение с данными пользователя и товарами из корзины
    response_message = (
        f'Ваш заказ принят!✅\n'
        f'👤ФИО: {user_data["name"]}\n'
        f'🚛Адрес доставки: {user_data["address"]}\n'
        f'☎️Номер телефона: {user_data["phone"]}\n'
        f'🗂Email: {user_data["email"]}\n'
        f'🚀Желаемая дата и время доставки: {user_data["delivery_datetime"]}\n\n'
        f'Товары в заказе:\n'
    )

    total_price = 0
    items_text = ""
    for basket_item, item, model, color, screen_size, memory, connectivity, ram in basket_items:
        item_total_price = float(item.price) * basket_item.quantity
        items_text += f"{model.name} ({basket_item.quantity} шт.)\n" \
                      f"Цвет: {color.name}\n"

        if screen_size:
            items_text += f"Размер экрана: {screen_size.size}\n"

        if memory:
            items_text += f"Память: {memory.size}\n"

        if model.category_id == IPAD_CATEGORY_ID:
            items_text += f"Тип соединения: {connectivity.type}\n"

        if model.category_id == MACBOOK_CATEGORY_ID:
            items_text += f"Оперативная память: {ram.size}\n"

        items_text += f"Цена: {item.price} руб.\n" \
                      f"Сумма: {item_total_price} руб.\n\n"
        total_price += item_total_price

    items_text += f"Общая стоимость: {total_price} руб.\n\n"
    response_message += items_text
    response_message += f'Благодарим Вас за оформление заказа! В ближайшее время наш менеджер выйдет с Вами на связь'

    # Добавляем информацию о товарах в user_data
    user_data["items"] = items_text

    # Очистка корзины пользователя
    await rq.clear_basket(message.from_user.id)

    await message.answer(response_message, reply_markup=main_keyboard)
    await state.clear()

    # Отправка уведомлений администраторам
    await notify_admins(bot, user_data)


async def save_order_to_db(user_id: int, data: dict):
    async with async_session() as session:
        order = Order(
            user_id=user_id,
            name=data['name'],
            address=data['address'],
            phone=data['phone'],
            email=data['email'],
            delivery_datetime=data['delivery_datetime']
        )
        session.add(order)
        await session.commit()


async def cancel_order(message: Message, state: FSMContext):
    await message.answer('Оформление заказа отменено.', reply_markup=kb.main_keyboard)
    await state.clear()

handlers_router = order_router
