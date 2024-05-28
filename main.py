import mysql.connector.cursor

import mysql.connector

from src import process_scraper as tjmg

# criar conexao mysql
connector = mysql.connector.connect(
    host=' ',
    user=' ',
    password=' ',
    database= ' ',
    charset='utf8mb4',
    connect_timeout=10
)
cursor = connector.cursor()

#test
tjmg.get_processo_table_essentials_file("xurrasco.txt", connection=connector, cursor=cursor)