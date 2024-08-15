import os
import mysql.connector
from typing import Dict, Optional
from dotenv import load_dotenv
from mysql.connector import Error, MySQLConnection
from src import process_scraper as tjmg


def load_env_vars() -> Dict[str, str]:
    load_dotenv()
    return {
        'db_host': os.getenv('DB_HOST'),
        'db_user': os.getenv('DB_USER'),
        'db_password': os.getenv('DB_PASSWORD'),
        'db_name': os.getenv('DB_NAME'),
        'db_table': os.getenv('DB_TABLE')
    }


def connect_to_database(config: Dict) -> Optional[MySQLConnection]:
    try:
        connection = mysql.connector.connect(
            host=config['db_host'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name'],
            charset='utf8mb4',
            connect_timeout=10
        )
        if connection.is_connected():
            print('Database connection established successfully.')
            return connection
    except Error as e:
        print(f'Error connecting to database: {e}')
        return None


if __name__ == '__main__':
    env_config = load_env_vars()
    connector = connect_to_database(env_config)
    cursor = connector.cursor()

    tjmg.get_processo_table_essentials_file('test.txt', connection=connector, cursor=cursor)
