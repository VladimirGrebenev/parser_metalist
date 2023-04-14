"""Сборщик прайсов с сайта"""

from bs4 import BeautifulSoup
import requests
import pandas as pd
import os

# ссылка на страницу со ссылками на прайсы
price_url = 'https://mc.ru/price/msk#'
# паттерн для поиска ссылок на прайсы
price_pattern = 'https://mc.ru/prices/'
# процент увеличения цены в прайсе
percent_up = 1


def main():
    """Главная функция запуска сборщика прайсов"""
    price_links_dict = get_price_links(price_url, price_pattern)
    for title, link in price_links_dict.items():
        tables_list = parse_price_link(link)
        parse_tables(tables_list, title)


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
        headers.append('категория')
        for el in table.find_all('th'):
            title = el.text
            headers.append(title)

        # фиксируем подкатегории
        sub_category = str(headers[1]).replace('/', '-')

        # меняем название второй колонки
        headers[1] = 'подкатегория'

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
                if n == 0 and item.text.startswith(tuple('0123456789')):
                    item = round(float(item.text.replace(',', '.')), 2)
                    item = item + (item / 100 * percent_up)
                    table_row.append(item)
                else:
                    table_row.append(item.text.replace(';', ',').strip())
            length = len(mydata)
            mydata.loc[length] = table_row

        # Export to csv
        price_path = f'./price/'
        if not os.path.exists(price_path):
            os.makedirs(price_path)
        mydata.to_csv(fr'./price/{m_category}-{sub_category}', index=False)


if __name__ == '__main__':
    main()
