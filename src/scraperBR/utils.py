import re
import os
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import time

def expand(expression: str) -> list[str]:
    """
    Transforms a complex search expression with logical operators into a list
    of all possible combinations that, when searched together, are equivalent 
    to the original expression.
    
    Handles nested parentheses, AND (E) and OR (OU) operators.
    Supports multi-line expressions and flexible spacing.
    
    Args:
        expression: A search expression string with operators "E" (AND) and "OU" (OR)
                   and parentheses for grouping. Can include newlines and extra spaces.
    
    Returns:
        List of strings representing all possible term combinations
    
    Example:
        >>> expr = "(((doença OU doenças) E (rara OU raras)) OU ((medicamento) E (órfão)))"
        >>> expand(expr)
        ['doença rara', 'doença raras', 'doenças rara', 'doenças raras', 'medicamento órfão']
        
        Multi-line example:
        >>> expr_multiline = '''
        ... (((doença OU síndrome) E (rara OU ultrarrara)) OU (medicamento E órfão))
        ... '''
        >>> expand(expr_multiline)
        ['doença rara', 'doença ultrarrara', 'medicamento órfão', 'síndrome rara', 'síndrome ultrarrara']
    """
    # Normaliza a expressão: remove quebras de linha e normaliza espaços
    expression = re.sub(r'\s+', ' ', expression)
    
    # Valida parênteses
    if '()' in expression:
        raise ValueError("Parênteses vazios não permitidos")
    if expression.count('(') != expression.count(')'):
        raise ValueError("Parênteses desequilibrados na expressão")
    
    # Normalize the expression: convert to standard symbols
    expr = expression.replace(" E ", " AND ").replace(" OU ", " OR ")
    
    def tokenize(expression: str) -> list[str]:
        """Convert expression to a list of tokens (terms, operators, parentheses)"""
        # First, insert spaces around parentheses to make them separate tokens
        expr_with_spaces = re.sub(r'([()])', r' \1 ', expression)
        # Split by whitespace and filter out empty strings
        tokens = [token for token in expr_with_spaces.split() if token]
        return tokens
    
    def parse_expression(tokens: list[str]) -> list[str]:
        """Parse expression using a recursive descent parser"""
        def parse_or() -> list[str]:
            left = parse_and()
            while i[0] < len(tokens) and tokens[i[0]] == "OR":
                i[0] += 1  # Consume "OR"
                right = parse_and()
                left = left + right  # Union of sets for OR operation
            return left
        
        def parse_and() -> list[str]:
            left = parse_primary()
            while i[0] < len(tokens) and tokens[i[0]] == "AND":
                i[0] += 1  # Consume "AND"
                right = parse_primary()
                # Cartesian product for AND operation
                product_result = []
                for l in left:
                    for r in right:
                        product_result.append(f"{l} {r}")
                left = product_result
            return left
        
        def parse_primary() -> list[str]:
            if i[0] >= len(tokens):
                return []
            
            if tokens[i[0]] == "(":
                i[0] += 1  # Consume "("
                result = parse_or()
                if i[0] < len(tokens) and tokens[i[0]] == ")":
                    i[0] += 1  # Consume ")"
                return result
            else:
                # It's a term (a word)
                term = tokens[i[0]]
                i[0] += 1
                return [term]
        
        # Use a mutable index
        i = [0]
        return parse_or()
    
    # Clean up the tokens
    tokens = tokenize(expr)
    
    # Parse the expression
    result = parse_expression(tokens)
    
    # Remove duplicates and sort
    return sorted(list(set(result)))

def remove_duplicates(df: pd.DataFrame):
    df_copy = df.copy()

    # Identificar linhas duplicadas pela coluna 'link'
    duplicatas = df_copy[df_copy.duplicated(subset='link', keep=False)]

    # First, create the aggregation dictionary
    agg_dict = {'termo_busca': ', '.join}
    # Add other columns with 'first' aggregation
    agg_dict.update({col: 'first' for col in duplicatas.columns if col not in ['link', 'termo_busca']})

    # Now use the aggregation dictionary
    duplicatas_agrupadas = duplicatas.groupby('link').agg(agg_dict).reset_index()

    # Excluir as duplicatas do DataFrame original
    df_sem_duplicatas = df_copy.drop_duplicates(subset='link', keep=False)

    # Concatenar o DataFrame original com as duplicatas agrupadas
    novo_df = pd.concat([df_sem_duplicatas, duplicatas_agrupadas], ignore_index=True)

    return novo_df

def start_session():
    session = requests.Session()
    session.headers.update({
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt-BR,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
        })

    return session

def extract(df, col):
    session = start_session()
        
    lista_infos = []
    n_items = len(df)
    i = 1

    for link in df[col]:
        try:
            # Verifica se é um link do tipo file://
            if link.startswith('file://'):
                print(f'Pulando link de arquivo local: {link}')
                lista_infos.append('')  # Adiciona string vazia para manter o alinhamento dos dados
            else:
                requisicao = session.get(url=link)
                lista_infos.append(bs(requisicao.content).text.strip())
            
            time.sleep(1)
            print(f'{i}/{n_items}')
            i += 1
        except Exception as e:
            print(f'Erro ao processar link {link}: {str(e)}')
            lista_infos.append('')  # Adiciona string vazia em caso de erro

    df[f'{col}_content'] = lista_infos

    return df

def check(df):
    df_count = df.copy()
    
    set_of_words = set(' '.join(df_count.termo_busca.unique()).split())

    for word in set_of_words:
        # Regex melhorado para garantir que a palavra seja encontrada como palavra completa
        # Usa lookahead e lookbehind negativos para garantir que não há caracteres alfanuméricos antes ou depois
        pattern = r'(?<!\w)' + re.escape(word) + r'(?!\w)'
        df_count[word] = df_count.apply(lambda row: len(re.findall(pattern, row['link_content'].lower())), axis=1)

    return df_count