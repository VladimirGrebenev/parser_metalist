import time
import asyncio
from aiowc import API, APISession
import aiohttp
import json

from env import CONS_SEC, CONS_KEY, SITE_URL_UPLOAD
from load_data import import_products_from_csv, divide_list, delete_all_products, delete_all_categories

# Api Setup:
wcapi = API(
    url=SITE_URL_UPLOAD,  # Your store URL
    consumer_key=CONS_KEY,  # Your consumer key
    consumer_secret=CONS_SEC,  # Your consumer secret
    wp_api=True,  # Enable the WP REST API integration
    version="wc/v3",  # WooCommerce WP REST API version
    timeout=10000,

)

print(f"начало: {time.strftime('%X')}")
# print('Удаление продуктов...')
# delete_all_products()
# print(f"Продукты удалены: {time.strftime('%X')}")
# print('Удаление категорий...')
# delete_all_categories()
# print(f"Категории удалены: {time.strftime('%X')}")
# to_load = import_products_from_csv('test999.csv')
to_load = import_products_from_csv('price.csv')
print(f"Категории загуржены, прайс для загрузки готов: {time.strftime('%X')}")
divided_products = divide_list(to_load, 100)
print(f"Пакеты для загурзки сформированы: {time.strftime('%X')}")


async def send_to_api(data):
    async with APISession(wcapi) as session:
        res = await session.post('products/batch', data)
        res.close()


async def main(sublists_):
    tasks = []
    count = 0

    for sublist in sublists_:
        data = {
            "create": sublist
        }
        tasks.append(asyncio.create_task(send_to_api(data)))
        # await asyncio.sleep(3)

        if len(tasks) == 30:

            for task in tasks:
                await task
                count += 1
                tasks.remove(task)

            print(f"пакетов {count} загружено {time.strftime('%X')}")


asyncio.get_event_loop().run_until_complete(main(divided_products))
# asyncio.run(main(divided_products))
print(f"Загрузка завершена: {time.strftime('%X')}")
