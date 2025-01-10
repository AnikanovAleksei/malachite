from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from typing import List
from database.models import Model, Color, Memory, ScreenSize, Connectivity

from database import requests as rq


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Каталог'), KeyboardButton(text='Корзина')],
        [KeyboardButton(text='Связь с менеджером')],
        [KeyboardButton(text='Индивидуальный запрос')]
    ],
    resize_keyboard=True
)


def get_basket_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Корзина'), KeyboardButton(text='Каталог')],
            [KeyboardButton(text='Очистить корзину'), KeyboardButton(text='Оформить заказ')]
        ],
        resize_keyboard=True
    )
    return keyboard


# Главная инлайн-клавиатура
main_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Свяжитесь с менеджером', callback_data='connect')]
    ]
)

# Клавиатура для отправки номера телефона
get_number = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📱Отправить номер телефона', request_contact=True)],
    ],
    resize_keyboard=True
)


# Получение каталога из БД
async def get_catalog():
    all_categories = await rq.get_categories()
    builder = InlineKeyboardBuilder()

    for category in all_categories:
        builder.add(
            InlineKeyboardButton(
                text=category.name,
                callback_data=f'category_{category.id}'
            )
        )
    return builder.adjust(2).as_markup()


# Кнопка моделей из БД
async def get_models_keyboard(models: List[Model]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for model in models:
        builder.add(InlineKeyboardButton(text=model.name, callback_data=f'model_{model.id}'))
    builder.add(InlineKeyboardButton(text='🔙Назад', callback_data='back_to_categories'))
    return builder.adjust(1).as_markup()


# Кнопка цвета
async def get_colors_keyboard(colors: List[Color], category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for color in colors:
        builder.add(InlineKeyboardButton(text=color.name, callback_data=f'color_{color.id}'))
    builder.add(InlineKeyboardButton(text='🔙Назад', callback_data=f'back_to_models_{category_id}'))
    return builder.adjust(1).as_markup()


async def get_memory_keyboard(memories: List[Memory]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for memory in memories:
        builder.add(InlineKeyboardButton(text=memory.size, callback_data=f'memory_{memory.id}'))
    builder.add(InlineKeyboardButton(text='🔙Назад', callback_data='back_to_colors'))
    return builder.adjust(1).as_markup()


async def get_screen_size_keyboard(screen_sizes: List[ScreenSize]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for screen_size in screen_sizes:
        builder.add(InlineKeyboardButton(text=screen_size.size, callback_data=f'screen_size_{screen_size.id}'))
    builder.add(InlineKeyboardButton(text='🔙Назад', callback_data='back_to_colors'))
    return builder.adjust(1).as_markup()


def get_cancel_keyboard():
    keyboard = [
        [KeyboardButton(text="Отмена")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return reply_markup


async def get_ram_keyboard(rams):
    builder = InlineKeyboardBuilder()
    for ram in rams:
        button_text = f"{ram.size}"
        callback_data = f"ram_{ram.id}"
        builder.row(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    builder.row(InlineKeyboardButton(text="🔙Назад", callback_data="back_to_memory"))
    return builder.as_markup()


async def get_connection_keyboard(connectivities: List[Connectivity]):
    builder = InlineKeyboardBuilder()
    for connectivity in connectivities:
        button_text = f"{connectivity.type}"
        callback_data = f"connection_{connectivity.id}"
        builder.row(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    builder.row(InlineKeyboardButton(text="🔙Назад", callback_data="back_to_memory"))
    return builder.as_markup()


async def get_add_to_basket_keyboard(item_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Добавить в корзину", callback_data=f'add_to_basket_{item_id}'))
    return builder.as_markup()


def get_individual_request_keyboard():
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Написать менеджеру",
                                  url="https://t.me/malachite_aps?start=Индивидуальный запрос")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
        ]
    )
    return inline_kb
