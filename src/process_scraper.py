from os import getcwd
from time import sleep
import re

import mysql
import requests
from fitz import fitz
from src import number_scraper as ns


def remove_first_line(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()[1:]
        file.close()
    with open(filepath, 'w') as file:
        file.writelines(lines)
        file.close()


def get_inteiro_teor(numproc: str, dir = getcwd() + "/inteiros-teores", timeout=3, filename = None):

    # formatar o número processual
    parts = ns.get_numproc_numbers(numproc)
    print(parts)

    #  pegar o url do inteiro teor
    url = ("https://www5.tjmg.jus.br/jurisprudencia/relatorioEspelhoAcordao.do?inteiroTeor=true&ano="
           + parts[2] + "&ttriCodigo=" + parts[0] + "&codigoOrigem=" + parts[1] + "&numero=" + parts[3] +
           "&sequencial=" + parts[5] + "&sequencialAcordao=0")

    # setup do nome do arquivo e diretório
    if(filename is None):
        dir = dir + "/"
        for string in parts:
            dir = dir + string
        dir = dir + ".pdf"
    else:
        dir = dir + "/" +  filename + ".pdf"

    # debug
    print(dir)
    print(url)

    # fazer requisicão e pegar o seu resultado
    try:
        r = requests.get(url, allow_redirects=True, timeout=timeout)
        print(r)
    except:
        print("nao foi possivel fazer a requisicao.")
        raise Exception("request_error")
    open(dir, "wb").write(r.content)
    sleep(0.05)


def get_data_from_numproc(numproc, dir):
    data = [numproc]

    # fazer download do pdf do acórdão e o transformar em texto
    try:
        get_inteiro_teor(numproc, dir + "/temp", filename="acordao")
    except:
        return None, None

    acordao_txt = ''
    try:
        acordao_doc = fitz.open(dir + "/temp/acordao.pdf")
    except:
        return None, None
    for pagen in range(acordao_doc.page_count):
        page = acordao_doc.load_page(pagen)
        acordao_txt += page.get_text()

    # pegar a ementa e súmula do acórdão
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

    # concatenar o resto das informacões
    data.append(acordao)
    data.append(ementa)
    data.append(sumula)

    return data, acordao


def get_processo_table_essentials(numprocs, dir = getcwd() + "/processos", connection=None, cursor=None, returns = True, lowerbound: int = 700*5.5, upperbound: int = 4000*5.5, delay=0.15):
    """
    Faz a raspagem dos dados essenciais de uma lista de processos, retornando uma tabela (em forma de array OU em um banco de
    dados) com o número processual, acordao formatado, ementa formatada e sumula
    formatada.

    :param numprocs: str []:  lista dos números processuais a serem consultados
    :param dir: str: diretório para salvar dados temporários utilizados pelo scraper
    :param connection: connection: conexão do banco de dados no qual as informacoes serão armazenadas.
    :param cursor: cursor: cursor com o banco de dados no qual as informacões serão armazenadas.
    :param returns: bool: flag indicando se a funcao deverá retornar um array com as informacoes.
    :return: string array
    """
    if returns:
        table = []

    # checar se o banco de dados será utilizado, e, em caso positivo, fazer o seu setup.
    using_database = False
    if(connection is not None):
        insert_query = """
            INSERT INTO processo (numero_tjmg, acordao, ementa, sumula) VALUES 
            (%s, %s, %s, %s)
            """
        using_database = True

    for numproc in numprocs:
        sleep(delay)
        numproc_clean = numproc.replace("-", "").replace(".", "").replace("/", "")
        try:

            data, acordao = get_data_from_numproc(numproc, dir)
            if data is None:
                continue

            # checar se a ementa não passou do limite de caracteres
            if len(acordao) < lowerbound or len(acordao) > upperbound:
                print("nao passou :c")
                continue

            # fazer a insercao dos dados no banco de dados, se possível
            if using_database:
                print("usando bd")
                try:
                    cursor.execute(insert_query, data)
                    connection.commit()
                except mysql.connector.Error:
                    print("error inserting into table""")

            # colocar as informacoes na tabela, se possível
            if returns:
                print("concatenando à tabela")
                table.append(data)
        except Exception as e:
            print(e)
            continue
    # retornar, se possível
    if returns:
        return table


def get_processo_table_essentials_file(file, connection, cursor, dir=getcwd() + "/processos", lowerbound = 700*5.5, upperbound = 4000*5.5, delay=0.15):

    insert_query = """
            INSERT INTO processo (numero_tjmg, acordao, ementa, sumula) VALUES 
            (%s, %s, %s, %s)
            """

    # get numprocs from file

    failed_requests = 0
    failed_request_limit = 9
    with open(file, "r+") as f:
        numero = f.readline().strip("\n")
        remove_first_line(file)
        f.close()

    contador = 0
    while numero is not None:
        # get new numero
        with open(file, "r+") as f:
            numero = f.readline().strip("\n")
            remove_first_line(file)

        sleep(0.2)

        if failed_requests > failed_request_limit:
            input("Houveram mais do que 9 requisicões falhadas. Verifique sua conexão com a internet e pressione enter para continuar")
            failed_requests = 0

        # pegar as infos
        data, acordao = get_data_from_numproc(numero, dir)
        if data is None:
            failed_requests += 1
            continue

        # checar se a ementa não passou do limite de caracteres
        if len(acordao) < lowerbound or len(acordao) > upperbound:
            print("nao passou :c")
            continue

        print("usando bd")
        try:
            cursor.execute(insert_query, data)
            connection.commit()
            print("deu tudo certo")
            failed_requests = 0
        except mysql.connector.Error:
            failed_requests += 1
            print("error inserting into table " + failed_requests.__str__())
            continue


