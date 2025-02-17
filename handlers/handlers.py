import os
from aiogram.filters import CommandStart, or_f
from aiogram.types import Message, CallbackQuery
from aiogram import Router, types, F
from sqlalchemy import delete
from handlers.contact import router as manager_router
from handlers.help_handlers import router as helper
from filters.config import (IPHONE_CATEGORY_ID, IPAD_CATEGORY_ID, WATCH_CATEGORY_ID, PODS_CATEGORY_ID,
                            MACBOOK_CATEGORY_ID)
from dotenv import load_dotenv
from keyboards import keyboards as kb
from database import requests as rq
from database.models import async_session


load_dotenv()
TOKEN = os.getenv('TOKEN_ID')


router = Router()

router.include_router(helper)
router.include_router(manager_router)


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    async with async_session() as session:
        await rq.create_user_if_not_exists(session, message.from_user.id, message.from_user.username)

    await message.answer(
        text=(
            "Malachite — премиальный магазин техники Apple 🍏\n\n"
            "Добро пожаловать в Malachite — место, где стиль встречается с технологией! ✨ Мы предлагаем:\n\n"
            "💎 Эксклюзивный сервис — индивидуальный подход и забота о каждом клиенте.\n\n"
            "🎁 Премиальную упаковку для вашей техники Apple. Каждая покупка подчеркивает "
            "особенный подход — элегантность в каждой детали!\n\n"
            "⚙️ Высококлассное обслуживание от профессионалов, которые помогут вам выбрать идеальный продукт Apple.\n\n"
            "С нами вы получите не только топовые гаджеты, но и прекрасное настроение! 🚀"
        ),
        reply_markup=kb.main_keyboard
    )


@router.message(or_f(F.text == 'Каталог', F.text == '/menu'))
async def catalog(message: Message):
    await message.answer('Выберите категорию товара', reply_markup=await kb.get_catalog())


@router.callback_query(F.data.startswith('category_'))
async def category_selected(callback: CallbackQuery):
    category_id = int(callback.data.split('_')[1])
    device_type = ''
    if category_id == IPHONE_CATEGORY_ID:
        device_type = 'iPhone'
        models = await rq.get_models_by_category(IPHONE_CATEGORY_ID)
        await callback.message.answer(f'Выберите модель из категории: {device_type}',
                                      reply_markup=await kb.get_models_keyboard(models))
    elif category_id == IPAD_CATEGORY_ID:
        device_type = 'iPad'
        models = await rq.get_models_by_category(IPAD_CATEGORY_ID)
        await callback.message.answer(f'Выберите модель из категории: {device_type}',
                                      reply_markup=await kb.get_models_keyboard(models))
    elif category_id == WATCH_CATEGORY_ID:
        device_type = 'Watch'
        models = await rq.get_models_by_category(WATCH_CATEGORY_ID)
        await callback.message.answer(f'Выберите модель из категории: {device_type}',
                                      reply_markup=await kb.get_models_keyboard(models))
    elif category_id == PODS_CATEGORY_ID:
        device_type = 'AirPods'
        models = await rq.get_models_by_category(PODS_CATEGORY_ID)
        await callback.message.answer(f'Выберите модель из категории: {device_type}',
                                      reply_markup=await kb.get_models_keyboard(models))
    elif category_id == MACBOOK_CATEGORY_ID:
        device_type = 'MacBook'
        models = await rq.get_models_by_category(MACBOOK_CATEGORY_ID)
        await callback.message.answer(f'Выберите модель из категории: {device_type}',
                                      reply_markup=await kb.get_models_keyboard(models))
    else:
        await callback.message.answer('Нет подходящей модели')

    await callback.message.delete()

    if device_type:
        await callback.answer(f'Вы выбрали категорию: {device_type}')


user_context = {}


@router.callback_query(F.data.startswith('model_'))
async def model_selected(callback: CallbackQuery):
    try:
        model_id = int(callback.data.split('_')[1])
    except (ValueError, IndexError):
        await callback.message.answer("Некорректные данные запроса. Пожалуйста, попробуйте снова.")
        return

    model = await rq.get_model(model_id)
    if not model:
        await callback.message.answer('Извините, модель не найдена.')
        await callback.message.delete()
        return

    # Получение цветов для модели
    colors = await rq.get_models_colors(model_id)
    if not colors:
        await callback.message.answer(f'Цвета для модели {model.name} не найдены.')
        await callback.message.delete()
        return

    keyboard = await kb.get_colors_keyboard(colors, model.category_id)
    await callback.message.answer(f'Выберите цвет для модели: {model.name}', reply_markup=keyboard)
    await callback.message.delete()
    await callback.answer(f'Вы выбрали {model.name}')

    # Сохранение выбранной модели и категории в контекст пользователя
    if callback.from_user.id not in user_context:
        user_context[callback.from_user.id] = {}
    user_context[callback.from_user.id]['model_id'] = model_id
    user_context[callback.from_user.id]['category_id'] = model.category_id


@router.callback_query(F.data.startswith('color_'))
async def color_selected(callback: CallbackQuery):
    try:
        color_id = int(callback.data.split('_')[1])
    except (ValueError, IndexError):
        await callback.message.answer("Некорректные данные запроса. Пожалуйста, попробуйте снова.")
        return

    color = await rq.get_color(color_id)
    if not color:
        await callback.message.answer('Извините, цвет не найден.')
        await callback.message.delete()
        return

    # Сохранение выбранного цвета в контекст пользователя
    if callback.from_user.id not in user_context:
        user_context[callback.from_user.id] = {}
    user_context[callback.from_user.id]['color_id'] = color_id

    # Получение модели для выбранного цвета
    model = await rq.get_model_by_color(color_id)
    if not model:
        await callback.message.answer('Извините, модель не найдена.')
        await callback.message.delete()
        return

    # Проверка, нужно ли открывать клавиатуру с выбором памяти или размера экрана
    if model.category_id == WATCH_CATEGORY_ID:
        screen_sizes = await rq.get_screen_sizes_by_model(model.id)
        if not screen_sizes:
            await callback.message.answer(f'Размеры экрана для модели {model.name} не найдены.')
            await callback.message.delete()
            return

        screen_size_keyboard = await kb.get_screen_size_keyboard(screen_sizes)
        await callback.message.answer(f'Выберите размер экрана для модели: {model.name}',
                                      reply_markup=screen_size_keyboard)
    elif model.category_id in [IPHONE_CATEGORY_ID, IPAD_CATEGORY_ID, MACBOOK_CATEGORY_ID]:
        memories = await rq.get_memories_by_model(model.id)
        if not memories:
            await callback.message.answer(f'Память для модели {model.name} не найдена.')
            await callback.message.delete()
            return

        memory_keyboard = await kb.get_memory_keyboard(memories)
        await callback.message.answer(f'Выберите память для модели: {model.name}', reply_markup=memory_keyboard)
    elif model.category_id == PODS_CATEGORY_ID:
        # Получение товара для выбранного цвета и модели
        item = await rq.get_item_by_color_and_model(color.id, model.id)
        if not item:
            await callback.message.answer('Извините, товар временно не в наличии.')
            await callback.message.delete()
            return

        # Формирование сообщения с информацией о товаре
        message_text = f'Ваш товар:\n\n' \
                       f'Категория: {item.name}\n' \
                       f'Модель: {model.name}\n' \
                       f'Цвет: {color.name}\n' \
                       f'Цена: {item.price} руб.\n\n' \
                       f'Описание:\n{item.description}'

        await callback.message.answer(message_text)

        # Отправка клавиатуры с кнопкой добавления в корзину
        add_to_basket_keyboard = await kb.get_add_to_basket_keyboard(item.id)
        await callback.message.answer('Вы хотите добавить товар в корзину?', reply_markup=add_to_basket_keyboard)

    await callback.message.delete()
    await callback.answer(f'Вы выбрали {color.name}')


@router.callback_query(F.data.startswith('memory_'))
async def memory_selected(callback: CallbackQuery):
    try:
        memory_id = int(callback.data.split('_')[1])
    except (ValueError, IndexError):
        await callback.message.answer("Некорректные данные запроса. Пожалуйста, попробуйте снова.")
        return

    memory = await rq.get_memory(memory_id)
    if not memory:
        await callback.message.answer('Извините, память не найдена.')
        await callback.message.delete()
        return

    # Проверка наличия ключа callback.from_user.id в словаре user_context
    if callback.from_user.id not in user_context or 'color_id' not in user_context[callback.from_user.id]:
        await callback.message.answer('Пожалуйста, выберите цвет.')
        return

    # Получение цвета для выбранного товара и сохраненного цвета пользователя
    color = await rq.get_color(user_context[callback.from_user.id]['color_id'])
    if not color:
        await callback.message.answer('Извините, цвет не найден.')
        await callback.message.delete()
        return

    # Получение модели для выбранного цвета
    model = await rq.get_model_by_color(color.id)
    if not model:
        await callback.message.answer('Извините, модель не найдена.')
        await callback.message.delete()
        return

    # Сохранение выбранной памяти в контекст пользователя
    if callback.from_user.id not in user_context:
        user_context[callback.from_user.id] = {}
    user_context[callback.from_user.id]['memory_id'] = memory_id

    # Проверка, нужно ли открывать клавиатуру с выбором оперативной памяти
    if model.category_id == MACBOOK_CATEGORY_ID:
        rams = await rq.get_rams_by_model(model.id)
        if not rams:
            await callback.message.answer(f'Оперативная память для модели {model.name} не найдена.')
            await callback.message.delete()
            return

        ram_keyboard = await kb.get_ram_keyboard(rams)
        await callback.message.delete()
        await callback.message.answer(f'Выберите оперативную память для модели: {model.name}',
                                      reply_markup=ram_keyboard)
        await callback.answer(f'Вы выбрали {memory.size}')
    elif model.category_id == IPAD_CATEGORY_ID:
        # Получение типов подключения для выбранной модели
        connectivities = await rq.get_connectivities_by_model(model.id)
        if not connectivities:
            await callback.message.answer(f'Типы подключения для модели {model.name} не найдены.')
            await callback.message.delete()
            return

        # Отправка клавиатуры с выбором типа подключения
        connection_keyboard = await kb.get_connection_keyboard(connectivities)
        await callback.message.delete()
        await callback.message.answer(f'Выберите тип подключения для модели: {model.name}',
                                      reply_markup=connection_keyboard)
        await callback.answer(f'Вы выбрали {memory.size}')
    else:
        # Получение товара для выбранной памяти, цвета и модели
        item = await rq.get_item_by_memory_color_and_model(memory.id, color.id, model.id)
        if not item:
            await callback.message.answer('Извините, товар временно не в наличии.')
            await callback.message.delete()
            return

        # Формирование сообщения с информацией о товаре
        message_text = f'Ваш товар:\n\n' \
                       f'Категория: {item.name}\n' \
                       f'Модель: {model.name}\n' \
                       f'Цвет: {color.name}\n' \
                       f'Память: {memory.size}\n' \
                       f'Цена: {item.price} руб.\n\n' \
                       f'Описание:\n{item.description}'

        await callback.message.answer(message_text)

        # Отправка клавиатуры с кнопкой добавления в корзину
        add_to_basket_keyboard = await kb.get_add_to_basket_keyboard(item.id)
        await callback.message.answer('Вы хотите добавить товар в корзину?', reply_markup=add_to_basket_keyboard)

    await callback.message.delete()
    await callback.answer(f'Вы выбрали {memory.size}')


@router.callback_query(F.data.startswith('ram_'))
async def ram_selected(callback: CallbackQuery):
    try:
        ram_id = int(callback.data.split('_')[1])
    except (ValueError, IndexError):
        await callback.message.answer("Некорректные данные запроса. Пожалуйста, попробуйте снова.")
        return

    # Проверка наличия ключей 'color_id', 'memory_id' и 'model_id' в словаре user_context
    if (callback.from_user.id not in user_context or 'color_id' not in user_context[callback.from_user.id]
            or 'memory_id' not in user_context[callback.from_user.id]
            or 'model_id' not in user_context[callback.from_user.id]):
        await callback.message.answer('Пожалуйста, выберите модель, цвет и память.')
        return

    # Получение модели, цвета и памяти для выбранного товара и сохраненных значений пользователя
    model = await rq.get_model(user_context[callback.from_user.id]['model_id'])
    color = await rq.get_color(user_context[callback.from_user.id]['color_id'])
    memory = await rq.get_memory(user_context[callback.from_user.id]['memory_id'])
    if not model or not color or not memory:
        await callback.message.answer('Извините, модель, цвет или память не найдены.')
        await callback.message.delete()
        return

    # Получение выбранной оперативной памяти
    ram = await rq.get_ram(ram_id)
    if not ram:
        await callback.message.answer('Извините, оперативная память не найдена.')
        await callback.message.delete()
        return

    # Получение товара для выбранной модели, цвета, памяти и оперативной памяти
    item = await rq.get_item_by_model_memory_color_and_ram(model.id, memory.id, color.id, ram.id)
    if not item:
        await callback.message.answer('Извините, товар временно не в наличии.')
        await callback.message.delete()
        return

    # Формирование сообщения с информацией о товаре
    message_text = f'Ваш товар:\n\n' \
                   f'Категория: {item.name}\n' \
                   f'Модель: {model.name}\n' \
                   f'Цвет: {color.name}\n' \
                   f'Память: {memory.size}\n' \
                   f'Оперативная память: {ram.size}\n' \
                   f'Цена: {item.price} руб.\n\n' \
                   f'Описание:\n{item.description}'

    await callback.message.answer(message_text)

    # Отправка клавиатуры с кнопкой добавления в корзину
    add_to_basket_keyboard = await kb.get_add_to_basket_keyboard(item.id)
    await callback.message.answer('Вы хотите добавить товар в корзину?', reply_markup=add_to_basket_keyboard)

    await callback.message.delete()
    await callback.answer(f'Вы выбрали {ram.size}')


@router.callback_query(F.data.startswith('connection_'))
async def connection_selected(callback: CallbackQuery):
    try:
        connectivity_id = int(callback.data.split('_')[1])
    except (ValueError, IndexError):
        await callback.message.answer("Некорректные данные запроса. Пожалуйста, попробуйте снова.")
        return

    # Получение модели, цвета, памяти и типа подключения для выбранного товара и сохраненных значений пользователя
    model = await rq.get_model(user_context[callback.from_user.id]['model_id'])
    color = await rq.get_color(user_context[callback.from_user.id]['color_id'])
    memory = await rq.get_memory(user_context[callback.from_user.id]['memory_id'])
    connectivity = await rq.get_connectivity(connectivity_id)
    if not model or not color or not memory or not connectivity:
        await callback.message.answer('Извините, модель, цвет, память или тип подключения не найдены.')
        await callback.message.delete()
        return

    # Получение товара для выбранной модели, цвета, памяти и типа подключения
    item = await rq.get_item_by_memory_color_model_and_connectivity(memory.id, color.id, model.id, connectivity.id)
    if not item:
        await callback.message.answer('Извините, товар временно не в наличии.')
        await callback.message.delete()
        return

    # Формирование сообщения с информацией о товаре
    message_text = f'Ваш товар:\n\n' \
                   f'Категория: {item.name}\n' \
                   f'Модель: {model.name}\n' \
                   f'Цвет: {color.name}\n' \
                   f'Память: {memory.size}\n' \
                   f'Тип подключения: {connectivity.type}\n' \
                   f'Цена: {item.price} руб.\n\n' \
                   f'Описание:\n{item.description}'

    await callback.message.answer(message_text)

    # Отправка клавиатуры с кнопкой добавления в корзину
    add_to_basket_keyboard = await kb.get_add_to_basket_keyboard(item.id)
    await callback.message.answer('Вы хотите добавить товар в корзину?', reply_markup=add_to_basket_keyboard)

    await callback.message.delete()
    await callback.answer(f'Вы выбрали {connectivity.type}')


@router.callback_query(F.data.startswith('screen_size_'))
async def screen_size_selected(callback: CallbackQuery):
    try:
        screen_size_id = int(callback.data.split('_')[2])
    except (ValueError, IndexError):
        await callback.message.answer("Некорректные данные запроса. Пожалуйста, попробуйте снова.")
        return

    screen_size = await rq.get_screen_size(screen_size_id)
    if not screen_size:
        await callback.message.answer('Извините, размер экрана не найден.')
        await callback.message.delete()
        return

    # Проверка наличия ключа callback.from_user.id в словаре user_context
    if callback.from_user.id not in user_context or 'color_id' not in user_context[callback.from_user.id]:
        await callback.message.answer('Пожалуйста, выберите цвет.')
        return

    # Получение цвета для выбранного товара и сохраненного цвета пользователя
    color = await rq.get_color(user_context[callback.from_user.id]['color_id'])
    if not color:
        await callback.message.answer('Извините, цвет не найден.')
        await callback.message.delete()
        return

    # Получение модели для выбранного цвета
    model = await rq.get_model_by_color(color.id)
    if not model:
        await callback.message.answer('Извините, модель не найдена.')
        await callback.message.delete()
        return

    # Сохранение выбранного размера экрана в контекст пользователя
    if callback.from_user.id not in user_context:
        user_context[callback.from_user.id] = {}
    user_context[callback.from_user.id]['screen_size_id'] = screen_size_id

    # Получение товара для выбранного размера экрана, цвета и модели
    item = await rq.get_item_by_screen_size_color_and_model(screen_size.id, color.id, model.id)
    if not item:
        await callback.message.answer('Извините, товар временно не в наличии.')
        await callback.message.delete()
        return

    # Формирование сообщения с информацией о товаре
    message_text = f'Ваш товар:\n\n' \
                   f'Категория: {item.name}\n' \
                   f'Модель: {model.name}\n' \
                   f'Цвет: {color.name}\n' \
                   f'Размер экрана: {screen_size.size}\n' \
                   f'Цена: {item.price} руб.\n\n' \
                   f'Описание:\n{item.description}'

    await callback.message.answer(message_text)

    # Отправка клавиатуры с кнопкой добавления в корзину
    add_to_basket_keyboard = await kb.get_add_to_basket_keyboard(item.id)
    await callback.message.answer('Вы хотите добавить товар в корзину?', reply_markup=add_to_basket_keyboard)

    await callback.message.delete()
    await callback.answer(f'Вы выбрали {screen_size.size}')


# Обработка кнопки назад для возврата к категориям
@router.callback_query(F.data.startswith('back_to_categories'))
async def back_to_categories(callback: CallbackQuery):
    await callback.message.answer('Выберите категорию:', reply_markup=await kb.get_catalog())
    await callback.message.delete()
    await callback.answer('Вы вернулись к выбору категории')


# возвращение от цвета к выбору модели
@router.callback_query(F.data.startswith('back_to_models'))
async def back_to_models(callback: CallbackQuery):
    category_id = int(callback.data.split('_')[3])
    models = await rq.get_models_by_category(category_id)
    await callback.message.answer('Выберете модель:', reply_markup=await kb.get_models_keyboard(models))
    await callback.message.delete()
    await callback.answer('Вы вернулись к выбору модели')


# Возвращение от памяти к цвету
# Множество категорий, для которых разрешен возврат к выбору цвета
ALLOWED_CATEGORIES = {IPHONE_CATEGORY_ID, IPAD_CATEGORY_ID, MACBOOK_CATEGORY_ID, WATCH_CATEGORY_ID}


@router.callback_query(F.data == 'back_to_colors')
async def back_to_colors(callback: CallbackQuery):
    # Получение model_id и category_id из контекста пользователя
    user_data = user_context.get(callback.from_user.id)
    if user_data:
        model_id = user_data['model_id']
        category_id = user_data['category_id']

        # Проверка, можно ли вернуться к выбору цвета для текущей категории
        if category_id in ALLOWED_CATEGORIES:
            colors = await rq.get_models_colors(model_id)
            keyboard = await kb.get_colors_keyboard(colors, category_id)
            await callback.message.answer('Выберите цвет:', reply_markup=keyboard)
            await callback.message.delete()
            await callback.answer('Вы вернулись к выбору цвета')
        else:
            await callback.message.answer('Возврат к выбору цвета недоступен для этой категории.')
    else:
        await callback.message.answer('Не удалось вернуться к выбору цвета. Пожалуйста, начните сначала.')


@router.callback_query(F.data == 'back_to_memory')
async def back_to_memory(callback: CallbackQuery):
    # Получение модели для выбранного цвета
    color = await rq.get_color(user_context[callback.from_user.id]['color_id'])
    model = await rq.get_model_by_color(color.id)

    # Получение памяти для выбранной модели
    memories = await rq.get_memories_by_model(model.id)

    # Создание клавиатуры с выбором памяти
    memory_keyboard = await kb.get_memory_keyboard(memories)

    # Отправка сообщения с клавиатурой и удаление предыдущего сообщения
    await callback.message.edit_text(f'Выберите память для модели: {model.name}', reply_markup=memory_keyboard)
    await callback.answer('Вы вернулись к выбору памяти')


@router.callback_query(F.data.startswith('add_to_basket_'))
async def add_to_basket(callback: CallbackQuery):
    try:
        item_id = int(callback.data.split('_')[3])
    except (ValueError, IndexError):
        await callback.message.answer("Некорректные данные запроса. Пожалуйста, попробуйте снова.")
        return

    user_id = callback.from_user.id
    success = await rq.add_item_to_basket(user_id, item_id)

    if success:
        await callback.message.answer("Товар успешно добавлен в корзину.")
    else:
        await callback.message.answer("Извините, товар не найден.")

    await callback.answer()


@router.message(F.text == 'Корзина')
async def show_basket(message: Message):
    user_id = message.from_user.id
    basket_items = await rq.get_basket_items(user_id)

    if not basket_items:
        await message.answer("Ваша корзина пуста.", reply_markup=kb.get_basket_keyboard())
        return

    basket_text = "Ваша корзина:\n\n"
    total_price = 0
    for basket_item, item, model, color, screen_size, memory, connectivity, ram in basket_items:
        item_total_price = float(item.price) * basket_item.quantity
        basket_text += f"{model.name} ({basket_item.quantity} шт.)\n" \
                       f"Цвет: {color.name}\n"

        if screen_size:
            basket_text += f"Размер экрана: {screen_size.size}\n"

        if memory:
            basket_text += f"Память: {memory.size}\n"

        if model.category_id == IPAD_CATEGORY_ID:
            basket_text += f"Тип соединения: {connectivity.type}\n"

        if model.category_id == MACBOOK_CATEGORY_ID:
            basket_text += f"Оперативная память: {ram.size}\n"

        basket_text += f"Цена: {item.price} руб.\n" \
                       f"Сумма: {item_total_price} руб.\n\n"
        total_price += item_total_price

    basket_text += f"Общая стоимость: {total_price} руб."
    await message.answer(basket_text, reply_markup=kb.get_basket_keyboard())


@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    user_id = message.from_user.id
    main_keyboard = await kb.main_keyboard(user_id)
    # Отправляем сообщение с клавиатурой каталога
    await message.answer('Выберите категорию товара', reply_markup=await kb.get_catalog())

    # Обновляем клавиатуру на главное меню
    await message.answer('Или воспользуйтесь меню ниже', reply_markup=main_keyboard)


@router.message(F.text == 'Очистить корзину')
async def clear_basket(message: Message):
    user_id = message.from_user.id
    async with rq.async_session() as session:
        await session.execute(
            delete(rq.Basket).where(rq.Basket.user_id == user_id)
        )
        await session.commit()
    await message.answer("Ваша корзина очищена.", reply_markup=kb.main_keyboard)


@router.message(F.text == 'Индивидуальный запрос')
async def individual_request(message: Message):
    response_text = (
        "Кнопка \"Индивидуальный запрос\" предназначена для пользователей, \n"
        "которые хотят получить персонализированную услугу, ответ или решение, \n"
        "соответствующее их уникальным потребностям. \n\n"
        "Возможности:\n\n"
        "- Уточнить наличие любой техники, даже если она отсутствует в каталоге.\n\n"
        "- Узнать об устройствах, которые были сняты с производства.\n\n"
        "- Получить индивидуальное предложение под ваши требования.\n\n"
        "- Найти решение на основе нестандартных или специализированных запросов.\n\n"
        "Для получения консультации нажмите кнопку ниже, и наш специальный отдел поможет вам.\n\n"
        "При обращении используйте сообщение \"Индивидуальный запрос\"."
    )
    await message.answer(response_text, reply_markup=kb.get_individual_request_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == 'back_to_main')
async def back_to_main_menu(callback_query: CallbackQuery):
    await callback_query.message.delete()  # Удаление сообщения бота
    await callback_query.message.answer('Вы вернулись в основное меню.', reply_markup=kb.main_keyboard)
    await callback_query.answer()


@router.message(F.text == 'Назад')
async def back_to_main(message: Message):
    main_keyboard = await kb.get_main_keyboard()
    await message.answer('Добро пожаловать в основное меню', reply_markup=main_keyboard)
