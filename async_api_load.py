import time
import asyncio
import aiohttp
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


def delete_all_products(self):
    count = 0
    while True:
        params = {"per_page": "100"}
        response_get = self.wcapi.get("products", params=params).json()

        products_to_delete = [d['id'] for d in response_get]
        data = {'delete': products_to_delete}
        response_delete = self.wcapi.post("products/batch", data).json()
        count += len(products_to_delete)
        if len(products_to_delete) < 100:
            break
        else:
            print("Deleted products: " + str(count))

    print("")
    print("Deleted products: " + str(count))


def delete_all_categories(self):
    count = 0
    while True:
        params = {"per_page": "100"}
        response_get = self.wcapi.get("products/categories",
                                      params=params).json()

        categories_to_delete = [d['id'] for d in response_get]
        data = {'delete': categories_to_delete}
        response_delete = self.wcapi.post("products/categories/batch",
                                          data).json()
        count += len(categories_to_delete)
        if len(categories_to_delete) < 100:
            break
        else:
            print("Deleted categories: " + str(count))

    print("")
    print("Deleted categories: " + str(count))

def divide_list(lst, n):
    """функция разделения списка на списки по нужному количеству объектов"""
    divided_lists = []
    for i in range(0, len(lst), n):
        divided_lists.append(lst[i:i + n])
    return divided_lists


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
            title = f'{row[subcategory_index]} | {row[title_index]} | ед.изм.: {row[unit_index]}'
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
            data_product = {
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
                data_product['categories'].append({'id': subcategory_id})

            products.append(data_product)

        return products


# запускающая функция
async def main_load():
    async with aiohttp.ClientSession() as session:
        for products in divided_products:
            load_data = {
                "create": products
            }
            async with session.post(
                    'https://test.veneberg81.ru/wp-json/wc/v3/products/batch?consumer_key={CONS_KEY}&consumer_secret={CONS_SEC}&wp_api={True}&version={"wc/v3"}&timeout={10000}',
                    data=load_data):
                pass


if __name__ == '__main__':
    print(time.strftime('%X'))
    to_load_products = import_products_from_csv('test.csv')
    divided_products = divide_list(to_load_products, 100)
    asyncio.run(main_load())
    print(time.strftime('%X'))
