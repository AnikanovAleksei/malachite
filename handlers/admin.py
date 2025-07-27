# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from sqlalchemy import text
import csv
import os

from filters.config import ADMIN_IDS, prices_config
from database.models import async_session

router = Router()


@router.message(Command("export_prices"), F.from_user.id.in_(ADMIN_IDS))
async def export_prices(message: Message) -> None:
    """Экспорт цен с правильным разделением по колонкам"""
    async with async_session() as session:
        query = text("""
        SELECT 
            i.id,
            c.name AS category,
            m.name AS model,
            cl.name AS color,
            mem.size AS memory,
            ss.size AS screen_size,
            conn.type AS connectivity,
            r.size AS ram,
            i.price
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN models m ON i.model_id = m.id
        LEFT JOIN colors cl ON i.color_id = cl.id
        LEFT JOIN memory mem ON i.memory_id = mem.id
        LEFT JOIN screen_sizes ss ON i.screen_size_id = ss.id
        LEFT JOIN connectivities conn ON i.connectivity_id = conn.id
        LEFT JOIN RMA r ON i.ram_id = r.id
        ORDER BY i.id
        """)
        result = await session.execute(query)
        items = result.mappings().all()

    # Создаем CSV с явным разделением колонок
    os.makedirs(os.path.dirname(prices_config.EXPORT_DIR), exist_ok=True)

    with open(prices_config.EXPORT_DIR, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')  # Используем точку с запятой как разделитель

        # Заголовки колонок
        headers = [
            "ID", "Категория", "Модель", "Цвет",
            "Память", "Экран", "Подключение",
            "RAM", "Цена"
        ]
        writer.writerow(headers)

        # Данные
        for item in items:
            row = [
                item["id"],
                item.get("category", ""),
                item.get("model", ""),
                item.get("color", ""),
                item.get("memory", ""),
                item.get("screen_size", ""),
                item.get("connectivity", ""),
                item.get("ram", ""),
                item["price"]  # Цена всегда в последней колонке
            ]
            writer.writerow(row)

    await message.reply_document(
        document=FSInputFile(prices_config.EXPORT_DIR),
        caption="📊 Файл для редактирования цен\n"
                "Каждый параметр в своей колонке\n"
                "Редактируйте ТОЛЬКО колонку 'Цена'"
    )


@router.message(F.document, F.from_user.id.in_(ADMIN_IDS))
async def handle_price_file(message: Message):
    if not message.document or not message.document.file_name.endswith('.csv'):
        return

    file_path = f"/tmp/updated_prices.csv"
    await message.bot.download(message.document, destination=file_path)

    updates = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')  # Изменили на csv.reader
        headers = next(reader)  # Читаем заголовки

        # Проверяем структуру файла
        if 'Цена' not in headers or 'ID' not in headers:
            await message.answer("❌ Файл должен содержать колонки 'ID' и 'Цена'")
            os.remove(file_path)
            return

        price_col = headers.index('Цена')
        id_col = headers.index('ID')

        for row in reader:
            if len(row) <= max(price_col, id_col):
                continue

            try:
                updates.append({
                    "id": int(row[id_col]),
                    "price": str(row[price_col]).strip()
                })
            except (ValueError, IndexError):
                continue

    if not updates:
        await message.answer("⚠ Не найдено данных для обновления")
        os.remove(file_path)
        return

    async with async_session() as session:
        try:
            await session.execute(
                text("UPDATE items SET price = :price WHERE id = :id"),
                updates
            )
            await session.commit()
            await message.answer(f"✅ Обновлено цен: {len(updates)}")
        except Exception as e:
            await session.rollback()
            await message.answer(f"❌ Ошибка базы данных: {str(e)}")
        finally:
            os.remove(file_path)
