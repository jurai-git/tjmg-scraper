import os
from os import getcwd
from time import sleep
import speech_recognition as sr
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_text_from_audio(audio_file):
    """
    Retorna o texto falado em um arquivo de áudio utilizando IA.

    :param audio_file: audio file
    :return: str
    """
    r = sr.Recognizer()
    with audio_file as source:
        audio_text = r.record(source)
        text = r.recognize_google(audio_text, language='pt-BR')
    return text


def get_nums_processuais(pesquisa_livre, lista_classe, data_inicio, data_final):
    """
    Scraper para coleta de números processuasis no TJMG.
    Recebe algumas informacões para a consulta processual (pesquisa livre, ID da classe processual, data mínima e data
    máxima, e retorna uma lista do python com todos os números processuais, sem formatacão.

    :param pesquisa_livre: str
    :param lista_classe: str
    :param data_inicio: str (DD%2FMM%2FYYYY)
    :param data_final: str (DD%2FMM%2FYYYY)
    :return: list of strings
    """

    url = ('https://www5.tjmg.jus.br/jurisprudencia/pesquisaPalavrasEspelhoAcordao.do;jsessionid'
           '=AC19FB65083C3B4D5D366A5CC1D1363C.juri_node1?numeroRegistro=1&totalLinhas=1&palavras={'
           'pesquisa_livre}&pesquisarPor=ementa&orderByData=2&codigoOrgaoJulgador=&codigoCompostoRelator=&classe'
           '=&listaClasse={lista_classe}&codigoAssunto=&dataPublicacaoInicial={data_inicial}&dataPublicacaoFinal={'
           'data_final}&dataJulgamentoInicial=&dataJulgamentoFinal=&siglaLegislativa=&referenciaLegislativa=Clique+na'
           '+lupa+para+pesquisar+as+refer%EAncias+cadastradas...&numeroRefLegislativa=&anoRefLegislativa=&legislacao'
           '=&norma=&descNorma=&complemento_1=&listaPesquisa=&descricaoTextosLegais=&observacoes=&linhasPorPagina'
           '=5000&pesquisaPalavras=Pesquisar')
    url = url.format(
        pesquisa_livre=pesquisa_livre,
        lista_classe=lista_classe,
        data_final=data_final,
        data_inicial=data_inicio
    )
    print(url)

    options = Options()
    options.set_preference('browser.download.folderList', 2)
    options.set_preference('browser.download.manager.showWhenStarting', False)
    options.set_preference('browser.download.dir', getcwd() + '/temp')
    driver = webdriver.Firefox(options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 6)
    captcha_file = getcwd() + '/temp'

    while True:
        try:
            wait.until(EC.presence_of_element_located((By.ID, 'captcha_text')))
        except:
            try:
                os.remove(captcha_file)
            except:
                pass
            break
        try:
            if os.path.isfile(captcha_file):
                os.remove(captcha_file)
                driver.find_element(By.ID, 'captcha_text').clear()
                driver.find_element(By.ID, 'gerar').click()
            driver.find_element(By.XPATH, '/html/body/table/tbody/tr[3]/td/table/tbody/tr[4]/td/a[2]').click()
            sleep(1)
            text = get_text_from_audio(sr.AudioFile(captcha_file))
            driver.find_element(By.ID, 'captcha_text').send_keys(text)
            sleep(1)
        except Exception as e:
            continue

    wait = WebDriverWait(driver, 10)

    numeros = []
    try:
        processos = driver.find_elements(By.CSS_SELECTOR, '.caixa_processo')
        i = 0
        for processo in processos:
            print(i)
            numeros.append(processo.find_element(By.CSS_SELECTOR, 'a > br + div').text)
            i += 1
    except Exception as e:
        print('deu errado :c')
        sleep(2)
    driver.quit()
    return numeros


def get_numproc_numbers(numproc: str):
    """
    Separador do número processual do TJMG em suas partes.
    Recebe um número processual do TJMG e retorna uma lista com todas as suas partes separadas.

    :param numproc: str
    :return: list of numprocs
    """

    parts = ['' for _ in range(6)]
    partsindex = 0
    lastindex = 0

    for i in range(len(numproc)):
        if numproc[i] == '.' or numproc[i] == '/' or numproc[i] == '-':
            parts[partsindex] = numproc[lastindex:i]
            partsindex += 1
            lastindex = i + 1
    parts[partsindex] = numproc[lastindex:len(numproc)]
    return parts
