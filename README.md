# tjmg-scraper
Um scraper básico para coleta de inteiros teores do Tribunal de Justica de Minas Gerais (TJMG)

# uso do scraper

A documentacão das funcões oferecidas pelo scraper estão no código fonte, mas aqui está uma lista geral delas:

get_nums_processuais: faz a coleta de todos os números processuais de uma busca avancada de jurisprudencia em segunda instância no TJMG.

get_processo_table: faz o download de diversas informacões de uma lista de números processuais. A lista das informacões a serem coletadas, em ordem, está na documentacao do código. A funcao retorna tanto um array do python com as infos, quando faz insert em um banco de dados.

get_inteiro_teor: faz o download do inteiro teor (ou acórdão) de um processo pelo seu número processual em pdf, no diretório informado.

normalize_tjmg_dataset: Faz a formatacão de acórdãos não formatadas, separando-as em acórdão, ementa, e súmula.


Exemplo:

```python
import mysql.connector as connector
import src.number_scraper as tjmg
import json

# pegar os números processuais de uma pesquisa sobre apelacao criminal
numeros = tjmg.get_num_processuais("Apelacao Cível", "9", "08%2F04%2F2023", "08%2F05%2F2023")
# salvar tudo em um arquivo de texto
with open("apelacao criminal/numprocs.txt", 'w') as file:
    file.write("\n".join(numeros))

# abrir o arquivo que acabamos de fazer com todos os números de processo
with open("apelacao criminal/numprocs.txt", "r") as file:
    entries = file.readlines()
entries = [entry.strip() for entry in entries]

# criar uma conexão no MySql
host = '111.222.333.4'
user = 'nome_usuario'
password = 'senha_usuario'
database = 'nome_db'
connection = connector.connect(host=host, user=user, password=password, port=3306, database=database)
cursor = connection.cursor()

# pegar a tabela de dados raspada pelo scraper. Vamos salvar tanto no banco de dados, passando a conexao e o cursor, 
# tanto em um array do python, setando o returns como True.
tabela = tjmg.get_processo_table(numprocs=entries, connection=connection, cursor=cursor, returns=True)

# fechar conexão com o banco de dados
if 'cursor' in locals():
    cursor.close()
if 'connection' in locals() and connection.is_connected():
    connection.close()

# transformar a tabela que pegamos em um arquivo json
with open("/apelacao criminal/processo.json", 'wb'):
    json.dump(tabela)
```

Nesse exemplo, fazemos a raspagem dos números processuais de uma busca sobre Apelacao Criminal, com cerca de 4500 processos, guardamos estes processos em um arquivo, e fazemos a raspagem e o download de todas as informacoes destes processos, guardando-as tanto em um banco de dados, quanto em um arquivo do tipo "json".

# dependências

a lista completa de requerimentos está no arquivo requirements.txt, mas as principais bibliotecas que você deverá ter são:

mysql

fitz (PyMuPDF)

SpeechRecognition

selenium

requests
