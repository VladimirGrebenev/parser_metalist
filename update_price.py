import csv
import time
from woocommerce import API
import logging

from env import CONS_SEC, CONS_KEY, SITE_URL_UPLOAD

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and set the log level and encoding
file_handler = logging.FileHandler('log_update_price.txt', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create a formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

# url для подключения к api
SITE_URL = SITE_URL_UPLOAD

# Api Setup:
wcapi = API(
    url=SITE_URL,  # Your store URL
    consumer_key=CONS_KEY,  # Your consumer key
    consumer_secret=CONS_SEC,  # Your consumer secret
    wp_api=True,  # Enable the WP REST API integration
    version="wc/v3",  # WooCommerce WP REST API version
    timeout=10000
)


def main_load():
    logger.info('обновление прайса запущено')
    # Вызов функций импорта товаров из CSV-файла
    update_new_price('price.csv')
    logger.info('прайс обновлён')


def update_new_price(csv_file):
    """функция обновления цены на сайте через API из файла CSV"""
    # Открываем файл CSV и читаем его
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        csv_data = csv.reader(csvfile)
        headers = next(csv_data)  # Заголовки столбцов CSV
        category_index = headers.index('Категория')
        subcategory_index = headers.index('Подкатегория')
        title_index = headers.index('Наименование (марка, ширина, размеры, полка, диаметр)')
        short_description_index = headers.index('Хар-ка (размер, диаметр, толщина, стенка, ширина, длина, полка)')
        unit_index = headers.index('Единица измерения')
        price_index = headers.index('Цена')

        # Проходим по каждой строке файла CSV
        for row in csv_data:
            product_name = f'{row[subcategory_index]} | {row[title_index]} | {row[short_description_index]} | {row[unit_index]}'
            new_price = row[price_index]

            # Получаем информацию о товаре по его имени
            products = wcapi.get("products", params={"search": product_name})

            if products.status_code == 200:
                products_data = products.json()

                # Проверяем, что найден хотя бы один товар с указанным именем
                if len(products_data) > 0:
                    product_id = products_data[0]['id']
                    old_price = products_data[0]['regular_price']

                    # Проверяем, изменилась ли цена товара
                    if has_price_changed(new_price, old_price):
                        update_product_price(product_id, new_price, product_name)
                    # else:
                    #     print(f"Цена товара '{product_name}' не изменилась. Не требуется обновление.")
                else:
                    # print(f"Товар с именем '{product_name}' не найден.")
                    sub_category_name = row[subcategory_index]  # ! в CSV есть столбец с названием подкатегории
                    category_name = row[category_index]  # ! в CSV есть столбец с названием подкатегории
                    create_new_product(category_name, sub_category_name, row, new_price, product_name)
            else:
                logger.info(f"Не удалось получить информацию о товаре '{product_name}'. Ошибка: {products.status_code}")


def has_price_changed(new_price, old_price):
    """Проверяет, изменилась ли цена товара"""
    if isinstance(new_price, str) and new_price == '':
        new_price = 0
    if isinstance(old_price, str) and old_price == '':
        old_price = 0
    return float(new_price) != float(old_price)


def update_product_price(product_id, new_price, product_name):
    """Обновляет цену товара"""
    data = {
        'regular_price': str(new_price)
    }
    response = wcapi.put(f"products/{product_id}", data)

    if response.status_code == 200:
        logger.info(f"Цена товара '{product_name}' успешно обновлена на {new_price}")
    else:
        logger.info(f"Не удалось обновить цену товара '{product_name}'. Ошибка: {response.status_code}")


def create_new_product(category_name, sub_category_name, row, new_price, product_name):
    """Создает новый товар"""
    # Ищем существует ли подкатегория
    categories = wcapi.get("products/categories", params={"search": sub_category_name})
    if categories.status_code == 200:
        categories_data = categories.json()
        if len(categories_data) > 0:
            subcategory_id = categories_data[0]['id']
            # Ищем существует ли категория
            categories = wcapi.get("products/categories", params={"search": category_name})
            if categories.status_code == 200:
                categories_data = categories.json()
                if len(categories_data) > 0:
                    category_id = categories_data[0]['id']
                    new_product_data = {
                        'name': product_name,
                        'regular_price': str(new_price),
                        'categories': [
                            {'id': category_id},
                            {'id': subcategory_id},
                        ],
                    }
                    response = wcapi.post("products", new_product_data)
                    if response.status_code == 201:
                        logger.info(
                            f"Создан новый товар '{product_name}' в категории '{category_name}' с ценой {new_price}")
                    else:
                        logger.info(
                            f"Не удалось создать новый товар '{product_name}'. Ошибка: {response.status_code}")
        else:
            # print(f"Подкатегория с именем '{sub_category_name}' не найдена.")
            categories = wcapi.get("products/categories", params={"search": category_name})
            if categories.status_code == 200:
                categories_data = categories.json()
                if len(categories_data) > 0:
                    category_id = categories_data[0]['id']
                    subcategory_data = {
                        'name': sub_category_name,
                        'parent': category_id,
                    }
                    response = wcapi.post("products/categories/", subcategory_data)
                    if response.status_code == 201:
                        category_data = response.json()
                        subcategory_id = category_data.get("id")
                        new_product_data = {
                            'name': product_name,
                            'regular_price': str(new_price),
                            'categories': [
                                {'id': category_id},
                                {'id': subcategory_id},
                            ],
                        }
                        response = wcapi.post("products", new_product_data)
                        if response.status_code == 201:
                            logger.info(
                                f"Создан новый товар '{product_name}' в категории '{sub_category_name}' с ценой {new_price}")
                        else:
                            logger.info(
                                f"Не удалось создать новый товар '{product_name}'. Ошибка: {response.status_code}")
                else:
                    # print(f"Родительская категория {category_name} тоже не найдена")
                    category_data = {
                        'name': category_name,
                        'parent': 0,
                    }
                    response = wcapi.post("products/categories", category_data)
                    if response.status_code == 201:
                        category_data = response.json()
                        category_id = category_data.get("id")
                        subcategory_data = {
                            'name': sub_category_name,
                            'parent': category_id,
                        }
                        response = wcapi.post("products/categories/", subcategory_data)
                        if response.status_code == 201:
                            category_data = response.json()
                            subcategory_id = category_data.get("id")
                            new_product_data = {
                                'name': product_name,
                                'regular_price': str(new_price),
                                'categories': [
                                    {'id': category_id},
                                    {'id': subcategory_id},
                                ],
                            }
                            response = wcapi.post("products", new_product_data)
                            if response.status_code == 201:
                                logger.info(
                                    f"Создан новый товар '{product_name}' в категории '{sub_category_name}' с ценой {new_price}")
                            else:
                                logger.info(
                                    f"Не удалось создать новый товар '{product_name}'. Ошибка: {response.status_code}")


if __name__ == '__main__':
    print(time.strftime('%X'))
    main_load()
    print(time.strftime('%X'))
