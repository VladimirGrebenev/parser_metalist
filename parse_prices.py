from bs4 import BeautifulSoup
import requests
import pandas as pd

price_url = 'https://mc.ru/price/msk#'
price_pattern = 'https://mc.ru/prices/'


def main():
    """Главная функция запуска"""
    price_links = get_price_links(price_url, price_pattern)
    for link in price_links:
        tables_list = parse_price_link(link)
        parse_tables(tables_list)


def get_price_links(prc_url, prc_ptn):
    """
    Функция принимает ссылку на страницу с прайсами и паттерн для поиска
    ссылок с прайсами. Возвращает список со ссылками на прайсы.
    :param prc_url: Ссылка на страницу 'https://mc.ru/price/msk#'
    :param prc_ptn: Паттерн ссылки 'https://mc.ru/price/msk#'
    :return: Список ссылок.
    """

    response = requests.get(prc_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    soup_links = soup.find('ul', class_='pagePriceList').find_all('a')
    price_links = []

    for link in soup_links:
        if link.get('href') and link.get('href').startswith(prc_ptn) \
                and link.get('href')[-4:] == '.htm':
            price_links.append(link.get('href'))

    return price_links


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


def parse_tables(t_list):
    """
    Функция парсит таблицы и записывает каждую в отдельный файл csv
    :param t_list: Список таблиц в HTML
    """

    # создаём заголовки таблиц
    for table in t_list:
        headers = []
        for el in table.find_all('th'):
            title = el.text
            headers.append(title)

        # фиксируем категорию
        category = str(headers[0]).replace('/', '-')

        # меняем название первой колонки
        headers[0] = 'категория'

        # Create a dataframe
        mydata = pd.DataFrame(columns=headers)

        for d in table.find_all('tr')[2:]:
            row_data = d.find_all('td')
            table_row = []
            table_row.append(category)
            for item in row_data:
                table_row.append(item.text)
            length = len(mydata)
            mydata.loc[length] = table_row

        # Export to csv
        mydata.to_csv(fr'./price/{category}', index=False)


if __name__ == '__main__':
    main()
