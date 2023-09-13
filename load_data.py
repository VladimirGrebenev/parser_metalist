import time
import csv
from woocommerce import API
from env import CONS_SEC, CONS_KEY, SITE_URL_UPLOAD

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


# запускающая функция
def main_load():
    # Вызов функций импорта товаров из CSV-файла
    to_load = import_products_from_csv('test_10.csv')
    print('список словарей товаров подготовлен')
    # отправка в базу пакетов 100 записей
    api_batch_sending(to_load)


def divide_list(lst, n):
    """функция разделения списка на списки по нужному количеству объектов"""
    divided_lists = []
    for i in range(0, len(lst), n):
        divided_lists.append(lst[i:i + n])
    return divided_lists


def api_batch_sending(products):
    """функция отправки пакетов, принимает на вход список с словарями товаров"""

    # разделяем список с товарами на пакеты по 100
    divided_products = divide_list(products, 100)

    # отправка пакетов
    n = 0  # счётчик пакетов
    for sublist in divided_products:

        data = {
            "create": sublist
        }

        response = wcapi.post("products/batch", data).json()

        n += 1

        if 'message' in response:
            print('Ошибка при импорте товаров:', response['message'])
        else:
            print(f'Пакет №{n} импротирован')


def import_products_from_csv(csv_file):
    """функция подготовки списка словарей товаров для инпорта через API из файла CSV"""

    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_data = csv.reader(file)
        headers = next(csv_data)  # Заголовки столбцов CSV
        category_index = headers.index('Категория')
        subcategory_index = headers.index('Подкатегория')
        title_index = headers.index('Наименование (марка, ширина, размеры, полка, диаметр)')
        short_description_index = headers.index('Хар-ка (размер, диаметр, толщина, стенка, ширина, длина, полка)')
        unit_index = headers.index('Единица измерения')
        price_index = headers.index('Цена')

        # Создание категорий
        category_mapping = {}
        # Создание подкатегорий
        subcategory_mapping = {}

        products = []

        for row in csv_data:
            # Индексирование данных из CSV
            category = row[category_index]
            subcategory = row[subcategory_index]
            title = f'{row[subcategory_index]} | {row[title_index]} | {row[short_description_index]} | {row[unit_index]}'
            price = float(row[price_index])


            # Создание категории, если ее нет
            if category not in category_mapping:
                category_data = {
                    'name': category,
                    'parent': 0  # При отсутствии родительской категории
                }
                created_category = wcapi.post("products/categories", category_data).json()
                category_mapping[category] = created_category['id']

            category_id = category_mapping[category]

            # Создание подкатегории, если есть
            if subcategory:
                if subcategory not in subcategory_mapping:
                    subcategory_data = {
                        'name': subcategory,
                        'parent': category_id
                    }
                    created_subcategory = wcapi.post("products/categories/", subcategory_data).json()
                    subcategory_mapping[subcategory] = created_subcategory['id']

                subcategory_id = subcategory_mapping[subcategory]
            else:
                subcategory_id = None

            # Создание товара в WooCommerce
            data_product = {
                'name': title,
                'regular_price': price,
                'categories': [
                    {
                        'id': category_id
                    }
                ]
            }

            if subcategory_id:
                data_product['categories'].append({'id': subcategory_id})

            products.append(data_product)

        return products


if __name__ == '__main__':
    print(time.strftime('%X'))
    main_load()
    print(time.strftime('%X'))
