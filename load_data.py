"""Загрузчик данных в базу данных на сайт.
Данный код использует библиотеку mysql.connector для подключения к базе данных
WordPress и библиотеку wordpress_xmlrpc для работы с XMLRPC API.
В коде сначала подключаемся к базе данных WordPress и создаем XMLRPC клиент.
Затем загружаем CSV файл в медиабиблиотеку WordPress и получаем ссылку на него.
Далее получаем все идентификаторы товаров WooCommerce из базы данных
WordPress и для каждого товара обновляем его цену в базе данных WordPress.
Обратите внимание, что в данном примере мы обновляем цену каждого товара на
жестко заданное значение '10.00', но в реальном применении вы, вероятно,
захотите использовать данные из загруженного CSV файла. После завершения
работы код закрывает соединение с базой данных."""


import os
import mysql.connector
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.media import UploadFile

# Connect to the WordPress website's database
db = mysql.connector.connect(
    host="<database_host>",
    user="<database_username>",
    password="<database_password>",
    database="<database_name>"
)

# Create a XMLRPC WordPress client
client = Client('<website_url>/xmlrpc.php', '<wordpress_username>', '<wordpress_password>')

# Define the path of the CSV file to be uploaded
csv_file_path = '<path_to_csv_file>/woo_price.csv'

# Upload the CSV file to the WordPress media library
with open(csv_file_path, 'rb') as file:
    file_data = file.read()
    file_name = os.path.basename(csv_file_path)
    data = {
        'name': file_name,
        'type': 'text/csv'
    }
    media = UploadFile(data, file_data)
    media_id = client.call(UploadFile(media))

# Get the location of the WordPress media library
media_url = client.call('wp.getMediaItem', media_id)['source_url']

# Retrieve the WooCommerce product IDs from the WordPress database
cursor = db.cursor()
query = "SELECT ID FROM wp_posts WHERE post_type='product' AND post_status='publish';"
cursor.execute(query)
product_ids = cursor.fetchall()
cursor.close()

# Loop over each product and update the product price in the WordPress database
for product_id in product_ids:
    post = WordPressPost()
    post.id = product_id[0]
    post.custom_fields = [{'key': '_price', 'value': '10.00'}, {'key': '_regular_price', 'value': '10.00'}, {'key': '_sale_price', 'value': ''}]
    post.post_status = 'publish'
    client.call(post)

# Close the database connection
db.close()