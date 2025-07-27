import os

IPHONE_CATEGORY_ID = 1
IPAD_CATEGORY_ID = 2
WATCH_CATEGORY_ID = 3
PODS_CATEGORY_ID = 4
MACBOOK_CATEGORY_ID = 5
ADMIN_IDS = [1454714038, 2144211023]


# Новые настройки (добавляем в тот же файл)
class DbConfig:
    URL = os.getenv('SQLALCHEMY_URL')


class PricesConfig:
    EXPORT_DIR = "/tmp/prices_export.csv"


# Для удобства доступа
db_config = DbConfig()
prices_config = PricesConfig()
