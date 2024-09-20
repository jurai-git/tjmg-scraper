import os
from database import load_env_vars, connect_to_database
from tjmg_scraper import process_scraper as sc


def main():
    env_config = load_env_vars()
    connector = connect_to_database(env_config)
    cursor = connector.cursor()

    path = os.path.join(os.getcwd(), 'processos')

    if not os.path.exists(path):
        os.makedirs(os.path.join(path, 'temp'))

    sc.get_processo_table_essentials_file(
        'test.txt',
        connection=connector,
        cursor=cursor,
        path=path
    )


if __name__ == '__main__':
    main()
