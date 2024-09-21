import os
from database import load_env_vars, connect_to_database
from tjmg_scraper.Scraper import Scraper


def main():
    env_config = load_env_vars()
    connector = connect_to_database(env_config)
    cursor = connector.cursor()

    path = os.path.join(os.getcwd(), 'processos')

    if not os.path.exists(path):
        os.makedirs(os.path.join(path, 'temp'))

    Scraper.get_processo_table_essentials_file(
        'test.txt',
        connection=connector,
        cursor=cursor,
        db_table=env_config['db_table'],
        path=path
    )


if __name__ == '__main__':
    main()
