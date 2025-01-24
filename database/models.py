from sqlalchemy import String, BigInteger, ForeignKey, Integer, func, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker, AsyncSession
import os
from dotenv import load_dotenv
from datetime import datetime


# Загрузка переменных окружения
load_dotenv()

# Убедитесь, что переменная окружения SQLALCHEMY_URL установлена корректно
SQLALCHEMY_URL = os.getenv('SQLALCHEMY_URL')
if not SQLALCHEMY_URL:
    raise ValueError("SQLALCHEMY_URL is not set in environment variables")

# Создание асинхронного движка SQLAlchemy с пулом соединений
engine = create_async_engine(
    url=SQLALCHEMY_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    echo=True
)


# Создание сессии
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    userphone: Mapped[str] = mapped_column(String(15), nullable=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=True)  # Уникальное поле
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Связь с таблицей basket
    baskets: Mapped[list["Basket"]] = relationship('Basket', back_populates='user')
    # Связь с таблицей orders
    orders: Mapped[list["Order"]] = relationship('Order', back_populates='user')


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    delivery_datetime: Mapped[str] = mapped_column(String(100), nullable=True)

    # Связь с таблицей users
    user: Mapped["Users"] = relationship('Users', back_populates='orders')


class Admin(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger)


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))


class Model(Base):
    __tablename__ = 'models'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.id'))
    items: Mapped[list["Item"]] = relationship('Item', back_populates='model')


class Color(Base):
    __tablename__ = 'colors'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey('models.id'))
    items: Mapped[list["Item"]] = relationship('Item', back_populates='color')


class Memory(Base):
    __tablename__ = 'memory'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    size: Mapped[str] = mapped_column(String(50))
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey('models.id'))

    # Связь с таблицей items
    items: Mapped[list["Item"]] = relationship('Item', back_populates='memory')


class RMA(Base):
    __tablename__ = 'RMA'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    size: Mapped[str] = mapped_column(String(50))
    model_id:  Mapped[int] = mapped_column(Integer, ForeignKey('models.id'))
    items: Mapped[list["Item"]] = relationship('Item', back_populates='ram')


class ScreenSize(Base):
    __tablename__ = 'screen_sizes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    size: Mapped[str] = mapped_column(String(50))
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey('models.id'))

    # Связь с таблицей items
    items: Mapped[list["Item"]] = relationship('Item', back_populates='screen_size')


class Connectivity(Base):
    __tablename__ = 'connectivities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50))

    # Связь с таблицей items
    items: Mapped[list["Item"]] = relationship('Item', back_populates='connectivity')


class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(150))
    price: Mapped[str] = mapped_column(String(10), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.id'))
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey('models.id'))
    color_id: Mapped[int] = mapped_column(Integer, ForeignKey('colors.id'))
    memory_id: Mapped[int] = mapped_column(Integer, ForeignKey('memory.id'), nullable=True)
    screen_size_id: Mapped[int] = mapped_column(Integer, ForeignKey('screen_sizes.id'), nullable=True)
    connectivity_id: Mapped[int] = mapped_column(Integer, ForeignKey('connectivities.id'), nullable=True)
    image_url: Mapped[str] = mapped_column(String(250), nullable=True)
    ram_id: Mapped[int] = mapped_column(Integer, ForeignKey('RMA.id'), nullable=True)

    # Связь с таблицей basket
    baskets: Mapped[list["Basket"]] = relationship('Basket', back_populates='item')

    # Связь с таблицей connectivities
    connectivity: Mapped["Connectivity"] = relationship('Connectivity', back_populates='items')

    ram: Mapped["RMA"] = relationship('RMA', back_populates='items')

    # Связь с таблицей models
    model: Mapped["Model"] = relationship('Model', back_populates='items')

    # Связь с таблицей colors
    color: Mapped["Color"] = relationship('Color', back_populates='items')

    # Связь с таблицей screen_sizes
    screen_size: Mapped["ScreenSize"] = relationship('ScreenSize', back_populates='items')

    # Связь с таблицей memory
    memory: Mapped["Memory"] = relationship('Memory', back_populates='items')


class Basket(Base):
    __tablename__ = 'basket'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey('items.id'))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped["Users"] = relationship('Users', back_populates='baskets')
    item: Mapped["Item"] = relationship('Item', back_populates='baskets')


async def async_main():
    async with engine.begin() as conn:
        # Удаление всех таблиц
        # await conn.run_sync(Base.metadata.drop_all)
        # Создание всех таблиц заново
        await conn.run_sync(Base.metadata.create_all)
