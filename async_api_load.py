import time
import asyncio
import aiohttp

from env import CONS_SEC, CONS_KEY, SITE_URL_UPLOAD
from load_data import import_products_from_csv, divide_list, delete_all_products, delete_all_categories

consumer_key = CONS_KEY
consumer_secret = CONS_SEC


async def upload_product(session, product_data):
    url = 'https://test.veneberg81.ru/wp-json/wc/v3/products/batch'
    auth = aiohttp.BasicAuth(consumer_key, consumer_secret)
    headers = {'Content-Type': 'application/json', 'encoding': 'utf-8'}

    async with session.post(url, json=product_data, auth=auth, headers=headers, timeout=10000) as response:
        if response.status == 201 or response.status == 200:
            result = await response.json(content_type=None, encoding='utf-8')
            print("Uploaded 100 products")
            # return result  # You can do additional processing or error handling here if needed
        else:
            print(f"Error while uploading product: {response.status}")
            # Handle error here or just continue to the next product


async def main(sublists_):
    # Product data to upload

    async with aiohttp.ClientSession() as session:
        tasks = []
        for sublist in sublists_:
            data = {
                "create": sublist
            }
            task = asyncio.ensure_future(upload_product(session, data))
            tasks.append(task)

            if len(tasks) == 30:
                for task in tasks:
                    await task
                    tasks.remove(task)



print(f"старт файла asyn_api_load.py: {time.strftime('%X')}")
print(f"Подготовка прайса к загрузке: {time.strftime('%X')}")
to_load = import_products_from_csv('price.csv')
print(f"Категории загружены, прайс для загрузки готов: {time.strftime('%X')}")
divided_products = divide_list(to_load, 100)
print(f"Пакеты для загурзки сформированы: {time.strftime('%X')}")

print(f"начало загрузки товаров: {time.strftime('%X')}")
asyncio.get_event_loop().run_until_complete(main(divided_products))
print(f"конец загрузки товаров: {time.strftime('%X')}")
