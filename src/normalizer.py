import json
import os.path
import re


def verify_dir(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def normalize_tjmg_data_set(load_file: str, upload_file: str = None):
    """
    Leitor de inteiros teores provenientes do Tribunal Judiciário de Minas Gerais.\n
    Esta função recebe obrigatóriamente o caminho para um arquivo json, contendo as informações brutas do pdf dos
    inteiros teores em formato string, para então retornar os conteúdos principais da ementa, acórdão e súmula.

    Estrutura do Json: {'0': 'inteiro-teor-pdf-texto'}

    :param load_file: str
    :param upload_file: str
    :return: list of json
    """

    # Tenta ler o json
    try:
        with open(load_file, 'r', encoding='utf-8') as file:
            data_json = json.load(file)
    except Exception as e:
        print(e)

    # Padrões para o Regex
    pattern_list = [r'^.*?EMENTA:', r'(?<=\n)\d+(?=\n)', r'Tribunal de Justiça de Minas Gerais\n']

    # Dados principais
    data = []

    # Itera sobre cada dict python
    for key, value in data_json.items():
        # Remove os padrões dispensáveis básicos
        value = re.sub('|'.join(pattern_list), '', value, flags=re.DOTALL)

        # Encontra a ementa e separa as estrofes
        menu_text = re.sub(r'(.*?)A\s+C\s+Ó\s+R\s+D\s+Ã\s+O.*', r'\1', value, flags=re.DOTALL)
        split = menu_text.split('\n\n')

        # Retira, caso tenha mais de uma estrofe, informações dispensáveis
        menu_text = ' '.join(split[:-1]) if len(split) != 1 else menu_text.join(split)

        # Encontra e formata o acórdão
        judgment_text = re.sub(r'.*?V\sO\sT\sO\s+(.*?)SÚMULA.*', r'\1', value, flags=re.DOTALL)
        judgment_text = re.sub(r'\s+', ' ', judgment_text)

        # Encontra e formata a súmula
        summary_text = re.sub(r'.*?SÚMULA:+(.*?)', r'\1', value, flags=re.DOTALL)
        summary_text = re.sub(r'\s+', ' ', summary_text)

        # Constrói o dicionário com dados formatados
        data.append(
            {
                key: {
                    'ementa': menu_text.strip(),
                    'acordao': judgment_text.strip(),
                    'sumula': summary_text.strip()
                }
             }
        )

    # Serializa a estrutura para json
    data = json.dumps(data, ensure_ascii=False, indent=2)

    # Cria e escreve o arquivo json
    try:
        verify_dir(upload_file)

        with open(upload_file, 'w', encoding='utf-8') as file:
            file.write(data)
    except Exception as e:
        print(e)

    # Retorna a lista de json
    return data


