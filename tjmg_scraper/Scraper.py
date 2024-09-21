import os
import re
import fitz
import requests
from typing import Optional
from tjmg_scraper import number_scraper as ns
from time import sleep


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

        cleaned_data = Scraper.clean_data(acordao_txt)
        data.extend(cleaned_data)
        return data, cleaned_data[0]

    def clean_data(self, acordao_txt):
        pattern_list = [r'^.*?EMENTA:', r'(?<=\n)\d+(?=\n)', r'Tribunal de Justiça de Minas Gerais\n']
        data_pdf = re.sub('|'.join(pattern_list), '', acordao_txt, flags=re.DOTALL)

        ementa = re.sub(r'(.*?)A\s+C\s+Ó\s+R\s+D\s+Ã\s+O.*', r'\1', data_pdf, flags=re.DOTALL)
        ementa = ' '.join(ementa.split('\n\n')[:-1]) if ementa.split('\n\n') != 1 else ementa

        acordao = re.sub(r'.*?V\sO\sT\sO\s+(.*?)SÚMULA.*', r'\1', data_pdf, flags=re.DOTALL)
        sumula = re.sub(r'.*?SÚMULA:+(.*?)', r'\1', data_pdf, flags=re.DOTALL)

        ementa = re.sub(r'\s+', ' ', ementa)
        acordao = re.sub(r'\s+', ' ', acordao)
        sumula = re.sub(r'\s+', ' ', sumula)

        return [acordao, ementa, sumula]

