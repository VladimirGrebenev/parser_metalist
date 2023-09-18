"""Сборщик прайсов с сайта"""

from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
from pathlib import Path
import shutil
import csv



# ссылка на страницу со ссылками на прайсы
price_url = 'https://mc.ru/price/msk#'
# паттерн для поиска ссылок на прайсы
price_pattern = 'https://mc.ru/prices/'
# процент на который увеличиваем цены в прайсе
percent_up = 1.6


def main():
    """Главная функция запуска сборщика прайсов"""

    # путь до рабочей директории
    basedir = os.path.abspath(os.getcwd())
    # путь до папки с прайсами
    price_dir = os.path.abspath(os.path.join(basedir, './price'))

    # удаляем предыдущие прайсы, чтобы файл не разрастался
    prices_folder_delete(price_dir)

    price_links_dict = get_price_links(price_url, price_pattern)
    for title, link in price_links_dict.items():
        tables_list = parse_price_link(link)
        parse_tables(tables_list, title)


    csv_merger(price_dir, "price.csv", globmask="*.csv", chunksize=1000)
    # transform_data('price.csv', 'woo_price.csv')
    print('Новый прайс сформирован')


def prices_folder_delete(prices_folder_path):
    if os.path.exists(prices_folder_path):
        try:
            shutil.rmtree(prices_folder_path)
            print(f"Папка '{prices_folder_path}' и файлы успешно удалены.")
        except OSError as error:
            print(f"Ошибка при удалении папки '{prices_folder_path}': {error}")
    else:
        print(f"Папка '{prices_folder_path}' ещё не создана")
    if os.path.exists('price.csv'):
        os.remove('price.csv')
        print("Файл 'price.csv' успешно удален.")
    else:
        print("Файл 'price.csv' не существует в текущей директории.")

def get_price_links(prc_url, prc_ptn):
    """
    Функция принимает ссылку на страницу с прайсами и паттерн для поиска
    ссылок с прайсами. Возвращает словарь со ссылками на прайсы.
    :param prc_url: Ссылка на страницу 'https://mc.ru/price/msk#'
    :param prc_ptn: Паттерн ссылки 'https://mc.ru/prices/'
    :return: Словарь ссылок.
    """

    response = requests.get(prc_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    soup_links_titles = soup.find('ul', class_='pagePriceList').find_all(
        'li')[1:-1]
    soup_links = soup.find('ul', class_='pagePriceList').find_all('a')[2:-1]

    prc_links = []
    # названия главных категорий / названия ссылок
    title_links = []

    for title in soup_links_titles:
        if title.text:
            title_links.append(title.text.replace('XLS\nHtml\n', '').strip())

    for link in soup_links:
        if link.get('href') and link.get('href').startswith(prc_ptn) \
                and link.get('href')[-4:] == '.htm':
            prc_links.append(link.get('href'))

    price_links_dict = dict(zip(title_links, prc_links))

    return price_links_dict


def parse_price_link(link):
    """
    Функция принимает ссылку на страницу с прайсами и отдаёт список html
    таблиц.
    :param link: Ссылка на страницу с прайсами.
    :return: Список таблиц в html
    """

    # создаём список с таблицами
    price_link = link
    response = requests.get(price_link)
    soup = BeautifulSoup(response.content, 'html.parser')

    tables = soup.find_all('table')
    tables_list = []

    for table in tables:
        tables_list.append(table)

    return tables_list


def parse_tables(t_list, m_category):
    """
    Функция парсит таблицы и записывает каждую в отдельный файл csv
    :param t_list: словарь
    :param m_category:главная категория
    """

    # создаём заголовки таблиц
    for table in t_list:
        headers = []
        headers.append('Категория')
        for el in table.find_all('th'):
            title = el.text
            headers.append(title)

        # фиксируем подкатегории
        sub_category = str(headers[1]).replace('/', '-')
        sub_category = sub_category.replace(',', ' ').replace('   ', ' ').replace('  ', ' ').strip()

        # меняем названия колонок
        headers[1] = 'Подкатегория'
        headers[2] = 'Наименование (марка, ширина, размеры, полка, диаметр)'
        headers[3] = 'Хар-ка (размер, диаметр, толщина, стенка, ширина, ' \
                     'длина, полка)'
        headers[4] = 'Единица измерения'

        # Create a dataframe
        mydata = pd.DataFrame(columns=headers)

        for d in table.find_all('tr')[2:]:
            row_data = d.find_all('td')
            table_row = []
            table_row.append(m_category)
            table_row.append(sub_category)
            n = len(row_data)
            for item in row_data:
                n -= 1
                if m_category == 'Нержавеющий лист (розница)' and n == 1:
                    table_row.append('т')
                elif n == 0 and item.text.startswith(tuple('0123456789')):
                    item = int(item.text.partition(',')[0])
                    item = item + (item / 100 * percent_up)
                    item = (round(item))
                    table_row.append(item)
                elif item.text == 'звоните':
                    table_row.append(0)
                else:
                    table_row.append(item.text.replace(',', '|').replace(
                        ';', '|').replace('   ', ' ').replace('  ', ' ').strip())

            length = len(mydata)
            mydata.loc[length] = table_row

        # Export to csv
        price_path = f'./price/'
        if not os.path.exists(price_path):
            os.makedirs(price_path)
        mydata.to_csv(fr'./price/{m_category}-{sub_category}.csv', index=False)


def csv_merger(path, out_filename="res.csv", globmask="*.csv", chunksize=5000,
               **kwargs):
    """
    Функция объединяет все файлы-прайсы в один файл-прайс.
    :param path: Путь до папки с прайсами для объединения.
    :param out_filename: Имя итогового файла с прайсами.
    :param globmask: Маска для отбора файлов.
    :param chunksize: Размер чанка.
    """
    path = Path(path)
    need_header = True
    for f in path.glob(globmask):
        for chunk in pd.read_csv(f, chunksize=chunksize, **kwargs):
            chunk.to_csv(out_filename, index=False, header=need_header,
                         mode="a")
            need_header = False


# def transform_data(input_file, output_file):
#     with open(input_file, 'r', encoding='utf-8') as infile, \
#             open(output_file, 'w', encoding='utf-8', newline='') as outfile:
#         reader = csv.reader(infile)
#         writer = csv.writer(outfile)
#         header = []
#         header.append('Категории')
#         header.append('Имя')
#         header.append('Краткое описание')
#         header.append('Базовая цена')
#
#         writer.writerow(header)
#         for i, row in enumerate(reader):
#             if i == 0:
#                 continue
#             if row[5] == 'звоните':
#                 row[5] = '0'
#             new_row = [f'Каталог > {row[0]} > {row[1]}',
#                        f'{row[1]} {row[2]}|ед.изм.:{row[4]}',
#                        row[3],
#                        row[5]]
#             writer.writerow(new_row)


if __name__ == '__main__':
    main()
