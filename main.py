import os
import mysql.connector
from dotenv import load_dotenv
from src import process_scraper as tjmg

load_dotenv()

connector = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset='utf8mb4',
    connect_timeout=10
)
cursor = connector.cursor()

tjmg.get_processo_table_essentials_file('', connection=connector, cursor=cursor)
