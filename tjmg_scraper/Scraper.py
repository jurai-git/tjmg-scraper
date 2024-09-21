import os
import re
import fitz
import requests
import mysql.connector as mysql
from typing import Optional, List
from tjmg_scraper import number_scraper as ns
from time import sleep
from mysql.connector import Error


class Scraper:
    TIMEOUT = 3
    FILE_EXT = '.pdf'
    TEMP_DIR = os.path.join(os.getcwd(), 'inteiros-teores')
    PROCESSO_PATH = os.path.join(os.getcwd(), 'processos')

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

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        try:
            acordao_doc = fitz.open(pdf_path)
        except Exception:
            return None

        acordao_txt = ''
        for pagen in range(acordao_doc.page_count):
            page = acordao_doc.load_page(pagen)
            acordao_txt += page.get_text()

        return acordao_txt

    @staticmethod
    def get_data_from_numproc(numproc, path):
        data = [numproc]
        pdf_path = os.path.join(path, 'temp', 'acordao.pdf')

        try:
            Scraper.get_inteiro_teor(
                numproc,
                os.path.join(path, 'temp'),
                filename='acordao'
            )
        except Exception:
            return None, None

        acordao_txt = Scraper().extract_text_from_pdf(pdf_path)

        if acordao_txt is None:
            return None, None

        cleaned_data = Scraper().clean_data(acordao_txt)
        data.extend(cleaned_data)
        return data, cleaned_data[0]

    def clean_data(self, acordao_txt):
        pattern_list = [r'^.*?EMENTA:', r'(?<=\n)\d+(?=\n)', r'Tribunal de Justiça de Minas Gerais\n']
        data_pdf = re.sub('|'.join(pattern_list), '', acordao_txt, flags=re.DOTALL)

        ementa = re.sub(r'(.*?)A\s+C\s+Ó\s+R\s+D\s+Ã\s+O.*', r'\1', data_pdf, flags=re.DOTALL)
        split = ementa.split('\n\n')
        ementa = ' '.join(split[:-1]) if len(split) != 1 else ementa.join(split)
        ementa = re.sub(r'\s+', ' ', ementa)

        acordao = re.sub(r'.*?V\sO\sT\sO\s+(.*?)SÚMULA.*', r'\1', data_pdf, flags=re.DOTALL)
        sumula = re.sub(r'.*?SÚMULA:+(.*?)', r'\1', data_pdf, flags=re.DOTALL)

        ementa = re.sub(r'\s+', ' ', ementa)
        acordao = re.sub(r'\s+', ' ', acordao)
        sumula = re.sub(r'\s+', ' ', sumula)

        return [acordao, ementa, sumula]

    @staticmethod
    def get_processo_table_essentials(
            numprocs,
            path=PROCESSO_PATH,
            connection=None,
            cursor=None,
            returns=True,
            lowerbound: int = 385e1,
            upperbound: int = 22e3,
            delay=0.15
    ) -> Optional[List]:
        table = [] if returns else None
        using_database = bool(connection)

        insert_query = """
            INSERT INTO processo (numero_tjmg, acordao, ementa, sumula) VALUES 
            (%s, %s, %s, %s)
        """

        for numproc in numprocs:
            sleep(delay)
            numproc_clean = Scraper.clean_numproc(numproc)
            try:
                data, acordao = Scraper.get_data_from_numproc(numproc_clean, path)
                if data is None or not (lowerbound <= len(acordao) <= upperbound):
                    continue

                if using_database:
                    try:
                        cursor.execute(insert_query, data)
                        connection.commit()
                    except mysql.Error:
                        print('Error inserting into table')

                if returns:
                    table.append(data)
            except Exception as e:
                print(e)
                continue

        return table

    @staticmethod
    def clean_numproc(numproc):
        return numproc.replace('-', '').replace('.', '').replace('/', '')

    @staticmethod
    def get_processo_table_essentials_file(
            file,
            connection,
            cursor,
            path=PROCESSO_PATH,
            lowerbound=385e1,
            upperbound=22e3,
            max_fails=10
    ):
        path = path or os.path.join(os.getcwd(), 'processos')

        insert_query = """
            INSERT INTO processo (numero_tjmg, acordao, ementa, sumula) VALUES 
            (%s, %s, %s, %s)
        """

        failed_requests = 0
        while True:
            with open(file, 'r+') as f:
                numero = f.readline().strip('\n')
                if not numero:
                    break
                Scraper.remove_first_line(file)

            sleep(0.2)
            if failed_requests > max_fails:
                input('Too many failed requests. Check your internet connection and press enter to continue.')
                failed_requests = 0

            data, acordao = Scraper.get_data_from_numproc(numero, path)
            if data is None:
                failed_requests += 1
                continue

            if not (lowerbound <= len(acordao) <= upperbound):
                continue

            try:
                cursor.execute(insert_query, data)
                connection.commit()
                failed_requests = 0
                print('[ + ] Insert successful.')
            except Error:
                failed_requests += 1
                print(f'[ - ] Error inserting into table. Failed attempts: {failed_requests}.')
