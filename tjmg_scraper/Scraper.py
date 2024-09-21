import os
import re
import fitz
import requests
from typing import Optional
from tjmg_scraper import number_scraper as ns
from time import sleep
from mysql.connector import Error


class Scraper:
    TIMEOUT = 3
    FILE_EXT = '.pdf'
    PROCESSO_PATH = os.path.join(os.getcwd(), 'processos')
    TEMP_DIR = os.path.join(PROCESSO_PATH, 'temp')
    BASE_URL = 'https://www5.tjmg.jus.br/jurisprudencia/relatorioEspelhoAcordao.do'

    def __init__(self):
        self.session = requests.Session()

    def remove_first_line(self, file: str) -> None:
        with open(file, 'r+') as f:
            lines = f.readlines()[1:]
            f.seek(0)
            f.writelines(lines)
            f.truncate()

    def get_inteiro_teor(self, numproc: str, filename: str, path: str = TEMP_DIR, timeout: int = TIMEOUT) -> str:
        parts = ns.get_numproc_numbers(numproc)
        url = (
            f'{self.BASE_URL}?inteiroTeor=true&ano={parts[2]}&ttriCodigo={parts[0]}'
            f'&codigoOrigem={parts[1]}&numero={parts[3]}&sequencial={parts[5]}&sequencialAcordao=0'
        )
        path = os.path.join(path, filename)

        try:
            response = self.session.get(url, allow_redirects=True, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f'Error downloading PDF: {e}')

        with open(path, 'wb') as file:
            file.write(response.content)
        sleep(0.05)

        return path

    def extract_pdf_text(self, pdf_path: str) -> Optional[str]:
        try:
            with fitz.open(pdf_path) as pdf_doc:
                return ''.join([page.get_text() for page in pdf_doc])
        except Exception as e:
            print(f'Failed to open or read PDF file: {pdf_path}, Error: {e}')
            return None

    def fetch_and_parse_process_data(self, numproc: str, path: str = TEMP_DIR) -> tuple[Optional[list], Optional[str]]:
        try:
            pdf_path = self.get_inteiro_teor(numproc, 'acordao.pdf', path)
            acordao_txt = self.extract_pdf_text(pdf_path)
            if acordao_txt is None:
                return None, None

            cleaned_data = self.sanitize_acordao_text(acordao_txt)
            return [numproc] + cleaned_data, cleaned_data[1]
        except Exception as e:
            print(f'Error fetching or parsing process data: {e}')
            return None, None

    def sanitize_acordao_text(self, acordao_txt: str) -> list[str]:
        patterns = [
            r'^.*?EMENTA:',
            r'(?<=\n)\d+(?=\n)',
            r'Tribunal de Justiça de Minas Gerais\n'
        ]
        cleaned_text = re.sub('|'.join(patterns), '', acordao_txt, flags=re.DOTALL)

        ementa = re.sub(r'(.*?)A\s+C\s+Ó\s+R\s+D\s+Ã\s+O.*', r'\1', cleaned_text, flags=re.DOTALL)
        split = ementa.split('\n\n')
        ementa = ' '.join(split[:-1]) if len(split) != 1 else ementa.join(split)
        ementa = re.sub(r'\s+', ' ', ementa)

        acordao = re.sub(r'.*?V\sO\sT\sO\s+(.*?)SÚMULA.*', r'\1', cleaned_text, flags=re.DOTALL)
        sumula = re.sub(r'.*?SÚMULA:+(.*?)', r'\1', cleaned_text, flags=re.DOTALL)

        return [ementa.strip(), acordao.strip(), sumula.strip()]

    @staticmethod
    def format_process_number(numproc: str) -> str:
        return numproc.replace('-', '').replace('.', '').replace('/', '')

    def process_file_and_insert_data(
            self,
            file: str,
            connection,
            cursor,
            db_table: str,
            lowerbound: int = 3850,
            upperbound: int = 22000,
            max_fails: int = 10
    ) -> None:

        insert_query = f"""
            INSERT INTO {db_table} (numero_tjmg, acordao, ementa, sumula) 
            VALUES (%s, %s, %s, %s)
        """
        failed_requests = 0

        while True:
            with open(file, 'r+') as f:
                numero = f.readline().strip()
                if not numero:
                    break
                self.remove_first_line(file)

            sleep(0.2)

            if failed_requests >= max_fails:
                input('Too many failed requests. Check your internet connection.')
                failed_requests = 0

            data, acordao = self.fetch_and_parse_process_data(numero)
            if data is None:
                failed_requests += 1
                continue

            if not (lowerbound <= len(acordao) <= upperbound):
                continue

            try:
                cursor.execute(insert_query, data)
                connection.commit()
                print(f'[ + ] Inserted process {numero} successfully.')
                failed_requests = 0
            except Error as e:
                print(f'[ - ] Database insertion error: {e}')

                if e.errno == 1406:
                    data_length = {
                        'Number': len(data[0]),
                        'Acórdão': len(data[1]),
                        'Ementa': len(data[2]),
                        'Súmula': len(data[3])
                    }
                    print(f'Data Length: {data_length}')

    def run(self,
            file: str,
            connection,
            cursor,
            db_table: str,
            lowerbound: int = 3850,
            upperbound: int = 22000,
            max_fails: int = 10
        ):

        self.process_file_and_insert_data(file, connection, cursor, db_table, lowerbound, upperbound, max_fails)
