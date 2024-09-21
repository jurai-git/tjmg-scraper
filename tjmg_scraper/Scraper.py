import os
import re
import fitz
import mysql.connector as mysql
import requests
from tjmg_scraper import number_scraper as ns
from os import getcwd
from time import sleep
from mysql.connector import Error


class Scraper:
    TIMEOUT = 3
    FILE_EXT = '.pdf'
    TEMP_DIR = os.path.join(getcwd(), 'inteiros-teores')
    PROCESSO_PATH = os.path.join(getcwd(), 'processos')

    def __init__(self):
        pass

    @staticmethod
    def remove_first_line(file):
        with open(file, 'r') as f:
            lines = f.readlines()[1:]
        with open(file, 'w') as f:
            f.writelines(lines)

    @staticmethod
    def get_inteiro_teor(numproc: str, path=TEMP_DIR, timeout=TIMEOUT, filename=None):
        parts = ns.get_numproc_numbers(numproc)
        url = ('https://www5.tjmg.jus.br/jurisprudencia/relatorioEspelhoAcordao.do?inteiroTeor=true&ano='
               f'{parts[2]}&ttriCodigo={parts[0]}&codigoOrigem={parts[1]}&numero={parts[3]}&sequencial='
               f'{parts[5]}&sequencialAcordao=0')

        if filename is None:
            path = path + '/'
            for string in parts:
                path = path + string
            path = path + '.pdf'
        else:
            path = f'{path}/{filename}.pdf'

        try:
            response = requests.get(url, allow_redirects=True, timeout=timeout)
        except requests.RequestException:
            print('Failed to make a request.')
            raise Exception('request_error')

        with open(path, 'wb') as file:
            file.write(response.content)
        sleep(0.05)
