import csv
import time
import requests
from woocommerce import API
from pprint import pprint

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

def main_load():
    # Вызов функций импорта товаров из CSV-файла
    update_new_price('test_10.csv')
    print('прайс обновлён')

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
                    if float(new_price) != float(old_price):

                        # Создаем данные для обновления цены товара
                        data = {
                            'regular_price': str(new_price)
                        }

                        # Обновляем цену товара с найденным product_id
                        response = wcapi.put(f"products/{product_id}", data)

                        if response.status_code == 200:
                            print(f"Цена товара '{product_name}' успешно обновлена на {new_price}")
                        else:
                            print(f"Не удалось обновить цену товара '{product_name}'. Ошибка: {response.status_code}")
                    else:
                        print(f"Цена товара '{product_name}' не изменилась. Не требуется обновление.")
                else:
                    print(f"Товар с именем '{product_name}' не найден.")
                    category_name = row[subcategory_index]  # Предполагаем, что в CSV есть столбец с названием подкатегории
                    # Получаем информацию о категории по имени
                    categories = wcapi.get("products/categories", params={"search": category_name})
                    if categories.status_code == 200:
                        categories_data = categories.json()

                        # Проверяем, что найдена хотя бы одна категория с указанным именем
                        if len(categories_data) > 0:
                            category_id = categories_data[0]['id']
                            # Создаем данные для нового товара
                            new_product_data = {
                                'name': product_name,
                                'regular_price': str(new_price),
                                'categories': [{'id': category_id}],
                            }

                            # Создаем новый товар
                            response = wcapi.post("products", new_product_data)

                            if response.status_code == 201:
                                print(
                                    f"Создан новый товар '{product_name}' в категории '{category_name}' с ценой {new_price}")
                            else:
                                print(
                                    f"Не удалось создать новый товар '{product_name}'. Ошибка: {response.status_code}")
                        else:



            else:
                print(f"Не удалось получить информацию о товаре '{product_name}'. Ошибка: {products.status_code}")

if __name__ == '__main__':
    print(time.strftime('%X'))
    main_load()
    print(time.strftime('%X'))