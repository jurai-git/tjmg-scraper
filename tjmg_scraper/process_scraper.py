import os.path
import re
import fitz
import mysql
import requests
from tjmg_scraper import number_scraper as ns
from os import getcwd
from time import sleep
from mysql.connector import Error


def remove_first_line(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()[1:]
        file.close()
    with open(filepath, 'w') as file:
        file.writelines(lines)
        file.close()


def get_inteiro_teor(numproc: str, path=getcwd() + '/inteiros-teores', timeout=3, filename=None):
    parts = ns.get_numproc_numbers(numproc)
    print(parts)

    url = ('https://www5.tjmg.jus.br/jurisprudencia/relatorioEspelhoAcordao.do?inteiroTeor=true&ano='
           + parts[2] + '&ttriCodigo=' + parts[0] + '&codigoOrigem=' + parts[1] + '&numero=' + parts[3] +
           '&sequencial=' + parts[5] + '&sequencialAcordao=0')

    if filename is None:
        path = path + '/'
        for string in parts:
            path = path + string
        path = path + '.pdf'
    else:
        path = f'{path}/{filename}.pdf'

    print(path)
    print(url)

    try:
        response = requests.get(url, allow_redirects=True, timeout=timeout)
        print(response)
    except Exception as e:
        print('nao foi possivel fazer a requisicao.')
        raise Exception('request_error')
    open(path, 'wb').write(response.content)
    sleep(0.05)


def get_data_from_numproc(numproc, path):
    data = [numproc]

    try:
        get_inteiro_teor(numproc, path + '/temp', filename='acordao')
    except Exception as e:
        return None, None

    acordao_txt = ''
    try:
        acordao_doc = fitz.open(path + '/temp/acordao.pdf')
    except:
        return None, None
    for pagen in range(acordao_doc.page_count):
        page = acordao_doc.load_page(pagen)
        acordao_txt += page.get_text()

    pattern_list = [r'^.*?EMENTA:', r'(?<=\n)\d+(?=\n)', r'Tribunal de Justiça de Minas Gerais\n']

    data_pdf = re.sub('|'.join(pattern_list), '', acordao_txt, flags=re.DOTALL)

    ementa = re.sub(r'(.*?)A\s+C\s+Ó\s+R\s+D\s+Ã\s+O.*', r'\1', data_pdf, flags=re.DOTALL)
    split = ementa.split('\n\n')
    ementa = ' '.join(split[:-1]) if len(split) != 1 else ementa.join(split)
    ementa = re.sub(r'\s+', ' ', ementa)

    acordao = re.sub(r'.*?V\sO\sT\sO\s+(.*?)SÚMULA.*', r'\1', data_pdf, flags=re.DOTALL)
    acordao = re.sub(r'\s+', ' ', acordao)

    sumula = re.sub(r'.*?SÚMULA:+(.*?)', r'\1', data_pdf, flags=re.DOTALL)
    sumula = re.sub(r'\s+', ' ', sumula)

    data.append(acordao)
    data.append(ementa)
    data.append(sumula)

    return data, acordao


def get_processo_table_essentials(
        numprocs,
        path=getcwd() + '/processos',
        connection=None,
        cursor=None,
        returns=True,
        lowerbound: int=700*5.5,
        upperbound: int=4000*5.5,
        delay=0.15
):
    """
    Faz a raspagem dos dados essenciais de uma lista de processos, retornando uma tabela (em forma de array OU em um banco de
    dados) com o número processual, acordao formatado, ementa formatada e sumula
    formatada.

    :param numprocs: str []:  lista dos números processuais a serem consultados
    :param path: str: diretório para salvar dados temporários utilizados pelo scraper
    :param connection: connection: conexão do banco de dados no qual as informacoes serão armazenadas.
    :param cursor: cursor: cursor com o banco de dados no qual as informacões serão armazenadas.
    :param returns: bool: flag indicando se a funcao deverá retornar um array com as informacoes.
    :return: string array
    """
    if returns:
        table = []

    using_database = False
    if connection is not None:
        insert_query = """
            INSERT INTO processo (numero_tjmg, acordao, ementa, sumula) VALUES 
            (%s, %s, %s, %s)
            """
        using_database = True

    for numproc in numprocs:
        sleep(delay)
        numproc_clean = numproc.replace('-', '').replace('.', '').replace('/', '')
        try:
            data, acordao = get_data_from_numproc(numproc, path)
            if data is None:
                continue

            if len(acordao) < lowerbound or len(acordao) > upperbound:
                print('nao passou :c')
                continue

            if using_database:
                print('usando bd')
                try:
                    cursor.execute(insert_query, data)
                    connection.commit()
                except mysql.connector.Error:
                    print('error inserting into table')

            if returns:
                print('concatenando à tabela')
                table.append(data)
        except Exception as e:
            print(e)
            continue
    if returns:
        return table


def get_processo_table_essentials_file(
        file,
        connection,
        cursor,
        path=getcwd() + '/processos',
        lowerbound=385e1,
        upperbound=22e3,
        max_fails=10
):
    if not path:
        path = os.path.join(getcwd(), 'processos')

    insert_query = """
            INSERT INTO processos (numero_tjmg, acordao, ementa, sumula) VALUES 
            (%s, %s, %s, %s)
            """

    with open(file, 'r+') as f:
        numero = f.readline().strip('\n')
        remove_first_line(file)
        f.close()

    failed_requests = 0
    while numero is not None:
        with open(file, 'r+') as f:
            numero = f.readline().strip('\n')
            remove_first_line(file)

        sleep(0.2)

        if failed_requests > max_fails:
            input(
                'Houveram mais do que 9 requisicões falhadas. Verifique sua '
                'conexão com a internet e pressione enter para continuar.'
            )
            failed_requests = 0

        data, acordao = get_data_from_numproc(numero, path)
        if data is None:
            failed_requests += 1
            continue

        if len(acordao) < lowerbound or len(acordao) > upperbound:
            print('nao passou :c')
            continue

        print('usando bd')
        try:
            cursor.execute(insert_query, data)
            connection.commit()
            print('deu tudo certo')
            failed_requests = 0
        except Error:
            failed_requests += 1
            print(f'error inserting into table {failed_requests.__str__()}')
            continue
