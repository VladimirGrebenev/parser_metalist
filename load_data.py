from woocommerce import API
import csv
import pprint
import pandas as pd
from env import CONS_SEC, CONS_KEY

# url для подключения к api
SITE_URL = 'https://www.stalservis.online'

# Api Setup:
wcapi = API(
    url=SITE_URL,  # Your store URL
    consumer_key=CONS_KEY,  # Your consumer key
    consumer_secret=CONS_SEC,  # Your consumer secret
    wp_api=True,  # Enable the WP REST API integration
    version="wc/v3",  # WooCommerce WP REST API version
    timeout=10000
)


def main():
    # Вызов функции импорта товаров из CSV-файла
    import_products_from_csv('test.csv')


def import_products_from_csv(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_data = csv.reader(file)
        headers = next(csv_data)  # Заголовки столбцов CSV
        category_index = headers.index('Категория')
        subcategory_index = headers.index('Подкатегория')
        title_index = headers.index('Наименование (марка, ширина, размеры, полка, диаметр)')
        short_description_index = headers.index('Хар-ка (размер, диаметр, толщина, стенка, ширина, длина, полка)')
        unit_index = headers.index('Единица измерения')
        price_index = headers.index('Цена')

        number = 0  # количество экспортированных товаров

        # Создание категорий
        category_mapping = {}
        # Создание подкатегорий
        subcategory_mapping = {}

        for row in csv_data:
            # Индексирование данных из CSV
            category = row[category_index]
            subcategory = row[subcategory_index]
            title = row[subcategory_index] + ' | ' + row[title_index] + ' | ед.изм.: ' + row[unit_index]
            short_description = row[short_description_index]
            price = row[price_index]

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
            data = {
                'name': title,
                'short_description': short_description,
                'regular_price': price,
                'categories': [
                    {
                        'id': category_id
                    }
                ]
            }

            if subcategory_id:
                data['categories'].append({'id': subcategory_id})

            response = wcapi.post("products", data).json()
            number += 1

            if 'message' in response:
                print('Ошибка при импорте товара:', response['message'])
            else:
                print(f'Товар успешно импортирован №{number} {response["id"]}')


if __name__ == '__main__':
    main()
