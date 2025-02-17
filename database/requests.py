import logging
from sqlalchemy.exc import SQLAlchemyError
from aiogram import Bot
from database.models import (Category, Item, Basket, Model, Color, Memory, async_session, ScreenSize,
                             Connectivity, RMA, Users)
from sqlalchemy import select, delete
from typing import List
from filters.config import ADMIN_IDS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


async def get_categories() -> List[Category]:
    async with async_session() as session:
        return await session.scalars(select(Category))


async def get_models_by_category(category_id: int) -> List[Model]:
    async with async_session() as session:
        return await session.scalars(select(Model).where(Model.category_id == category_id))


async def get_models_colors(model_id: int) -> List[Color]:
    async with async_session() as session:
        return await session.scalars(select(Color).where(Color.model_id == model_id))


# Функция используется для получения одной модели по ее id.
async def get_model(model_id: int) -> Model:
    async with async_session() as session:
        return await session.get(Model, model_id)


async def get_all_models() -> List[Model]:
    async with async_session() as session:
        return await session.execute(select(Model)).scalars().all()


async def get_memory(memory_id: int) -> Memory:
    async with async_session() as session:
        return await session.get(Memory, memory_id)


async def get_memories_by_model(model_id: int) -> List[Memory]:
    async with async_session() as session:
        return await session.scalars(select(Memory).where(Memory.model_id == model_id))


async def get_model_by_color(color_id: int) -> Model:
    async with async_session() as session:
        subquery = select(Color.model_id).where(Color.id == color_id).scalar_subquery()
        return await session.scalar(select(Model).where(Model.id == subquery))


async def get_color(color_id: int) -> Color:
    async with async_session() as session:
        return await session.get(Color, color_id)


async def get_screen_sizes_by_model(model_id: int) -> List[ScreenSize]:
    async with async_session() as session:
        return await session.scalars(select(ScreenSize).where(ScreenSize.model_id == model_id))


async def get_model_by_memory(memory_id: int) -> Item:
    async with async_session() as session:
        model_id = await session.scalar(select(Memory.model_id).where(Memory.id == memory_id))
        return await session.scalar(select(Item).where(Item.model_id == model_id))


async def get_color_by_model(model_id: int) -> Color:
    async with async_session() as session:
        subquery = select(Color.id).where(Color.model_id == model_id).limit(1).scalar_subquery()
        return await session.scalar(select(Color).where(Color.id == subquery))


async def get_ram(ram_id: int) -> RMA:
    async with async_session() as session:
        return await session.scalar(select(RMA).where(RMA.id == ram_id))


async def get_rams_by_model(model_id: int) -> List[RMA]:
    async with async_session() as session:
        return await session.scalars(select(RMA).where(RMA.model_id == model_id))


async def get_screen_size(screen_size_id: int) -> ScreenSize:
    async with async_session() as session:
        result = await session.execute(select(ScreenSize).where(ScreenSize.id == screen_size_id))
        return result.scalar_one_or_none()


async def get_item_by_memory_and_color(memory_size, color_id):
    async with async_session() as session:
        item = await session.execute(
            select(Item)
            .join(Model, Item.model_id == Model.id)
            .join(Memory, Item.memory_id == Memory.id)
            .join(Color, Item.color_id == Color.id)
            .filter(Memory.size >= memory_size)
            .filter(Color.id == color_id)
            .order_by(Memory.size)
            .limit(1)
        )
        return item.scalar_one_or_none()


async def get_item_by_model_memory_color_and_ram(model_id: int, memory_id: int, color_id: int, ram_id: int) -> Item:
    async with async_session() as session:
        return await session.scalar(
            select(Item)
            .where(Item.model_id == model_id)
            .where(Item.memory_id == memory_id)
            .where(Item.color_id == color_id)
            .where(RMA.id == ram_id)
            .where(Item.model_id == RMA.model_id)
        )


async def get_item_by_memory_color_and_model(memory_id: int, color_id: int, model_id: int) -> Item:
    async with async_session() as session:
        return await session.scalar(
            select(Item)
            .where(Item.memory_id == memory_id)
            .where(Item.color_id == color_id)
            .where(Item.model_id == model_id)
        )


async def get_connectivities_by_model(model_id: int) -> List[Connectivity]:
    async with async_session() as session:
        return await session.scalars(
            select(Connectivity)
            .join(Item, Connectivity.items)
            .where(Item.model_id == model_id)
            .distinct()
        )


async def get_connectivity(connectivity_id: int) -> Connectivity:
    async with async_session() as session:
        result = await session.execute(select(Connectivity).where(Connectivity.id == connectivity_id))
        return result.scalar_one_or_none()


async def get_item_by_memory_color_model_and_connectivity(memory_id: int,
                                                          color_id: int, model_id: int, connectivity_id: int) -> Item:
    async with async_session() as session:
        result = await session.execute(
            select(Item)
            .where(Item.memory_id == memory_id)
            .where(Item.color_id == color_id)
            .where(Item.model_id == model_id)
            .where(Item.connectivity_id == connectivity_id)
        )
        return result.scalar_one_or_none()


async def get_item_by_screen_size_color_and_model(screen_size_id: int, color_id: int, model_id: int) -> Item:
    async with async_session() as session:
        result = await session.execute(
            select(Item)
            .where(Item.screen_size_id == screen_size_id)
            .where(Item.color_id == color_id)
            .where(Item.model_id == model_id)
        )
        return result.scalar_one_or_none()


async def get_item_by_color_and_model(color_id: int, model_id: int) -> Item:
    async with async_session() as session:
        result = await session.execute(
            select(Item)
            .where(Item.color_id == color_id)
            .where(Item.model_id == model_id)
        )
        return result.scalar_one_or_none()


# Обработка корзины
async def add_item_to_basket(user_id: int, item_id: int, quantity: int = 1):
    async with async_session() as session:
        # Проверка наличия пользователя и создание, если он не существует
        user = await session.get(Users, user_id)
        if not user:
            user = Users(id=user_id, username=f"user_{user_id}", userphone=None, telegram_id=None, email=None)
            session.add(user)
            await session.commit()

        # Проверка наличия товара
        item = await session.get(Item, item_id)
        if not item:
            return False

        # Проверка наличия товара в корзине
        basket_item = await session.execute(
            select(Basket).where(Basket.user_id == user_id).where(Basket.item_id == item_id)
        )
        basket_item = basket_item.scalar_one_or_none()

        if basket_item:
            # Обновление количества товара в корзине
            basket_item.quantity += quantity
        else:
            # Добавление нового товара в корзину
            basket_item = Basket(user_id=user_id, item_id=item_id, quantity=quantity)
            session.add(basket_item)

        await session.commit()
        return True


# Функция для получения товаров из корзины:
async def get_basket_items(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Basket, Item, Model, Color, ScreenSize, Memory, Connectivity, RMA)
            .join(Item, Basket.item_id == Item.id)
            .join(Model, Item.model_id == Model.id)
            .join(Color, Item.color_id == Color.id)
            .outerjoin(ScreenSize, Item.screen_size_id == ScreenSize.id)
            .outerjoin(Memory, Item.memory_id == Memory.id)
            .outerjoin(Connectivity, Item.connectivity_id == Connectivity.id)
            .outerjoin(RMA, Item.ram_id == RMA.id)
            .where(Basket.user_id == user_id)
        )
        return result.all()


# Функция для удаления товара из корзины:
async def remove_item_from_basket(user_id: int, item_id: int):
    async with async_session() as session:
        basket_item = await session.execute(
            select(Basket).where(Basket.user_id == user_id).where(Basket.item_id == item_id)
        )
        basket_item = basket_item.scalar_one_or_none()

        if basket_item:
            await session.delete(basket_item)
            await session.commit()
            return True
        return False


async def clear_basket(user_id: int):
    async with async_session() as session:
        await session.execute(delete(Basket).where(Basket.user_id == user_id))
        await session.commit()


async def create_user_if_not_exists(session: AsyncSession, telegram_id: int, username: str):
    try:
        async with session.begin():
            # Проверяем наличие пользователя по telegram_id
            result = await session.execute(select(Users).where(Users.telegram_id == telegram_id))
            user = result.scalar_one_or_none()

            if user:
                # Обновляем существующего пользователя
                user.username = username
            else:
                # Создаем нового пользователя
                user = Users(telegram_id=telegram_id, username=username)
                session.add(user)

            await session.commit()
    except IntegrityError:
        # Если возникает ошибка уникального ограничения, просто пропускаем её
        await session.rollback()


async def register_user(user_id: int):
    async with async_session() as session:
        user = await session.get(Users, user_id)
        if user:
            user.is_registered = True
            await session.commit()


async def get_all_users():
    try:
        async with async_session() as session:
            result = await session.execute(select(Users))
            users = result.scalars().all()
            return users
    except SQLAlchemyError as e:
        # Убрано логирование
        raise


async def notify_admins(bot: Bot, order_data: dict):
    for admin_id in ADMIN_IDS:
        message_text = (
            f"Новый заказ оформлен!\n"
            f"ФИО: {order_data['name']}\n"
            f"Адрес доставки: {order_data['address']}\n"
            f"Номер телефона: {order_data['phone']}\n"
            f"Email: {order_data['email']}\n"
            f"Желаемая дата и время доставки: {order_data['delivery_datetime']}\n\n"
            f"Товары в заказе:\n"
            f"{order_data['items']}"
        )
        await bot.send_message(admin_id, message_text)


async def send_message_to_all_users(bot: Bot, message_text: str):
    users = await get_all_users()
    for user in users:
        if user.telegram_id:  # Проверка на наличие telegram_id
            await bot.send_message(chat_id=user.telegram_id, text=message_text)
