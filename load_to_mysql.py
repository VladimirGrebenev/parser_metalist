from env import HOST, USER, PASSWORD, DATABASE, PORT
import mysql.connector
from sqlalchemy import create_engine

connection_string = f'mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'

engine = create_engine(connection_string)
connection = engine.connect()
result = connection.execute("SHOW TABLES")

for row in result:
    print(row)

connection.close()