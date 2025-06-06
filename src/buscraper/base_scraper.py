"""
Módulo base para funcionalidades de web scraping.

Este módulo fornece a classe base abstrata BaseScraper, que serve como fundamento
para construção de web scrapers de buscadores. Gerencia tarefas comuns
como gerenciamento de sessão, paginação, tentativas de requisição e operações de arquivo.

Exemplo de uso:
    class MeuScraper(BaseScraper):
        def __init__(self):
            super().__init__("meu_scraper")
            self.api_base = "https://api.exemplo.com/dados"
            self.type = 'json'  # ou 'html' se usar HTMLScraper

        def _set_query_base(self, **kwargs) -> dict[str, Any]:
            return {"consulta": kwargs.get("termo_busca")}

        def _find_n_pags(self, response) -> int:
            return response.json().get("total_paginas", 1)

        def _parse_page(self, path: str) -> pl.DataFrame:
            # Implementação da análise dos dados baixados
            ...
"""

from abc import ABC, abstractmethod
from typing import Any, Literal
from datetime import datetime
from tqdm import tqdm
import polars as pl
import requests
import os
import shutil
import time
import logging
import glob
import json
import tempfile

# Import utility functions
from .utils import remove_duplicates, create_download_dir


class BaseScraper(ABC):
    """Classe base para criação de web scrapers.
    
    Fornece funcionalidades comuns para tarefas de web scraping, incluindo
    gerenciamento de sessão, paginação, tentativas de requisição e operações
    de arquivo. As subclasses devem implementar os métodos abstratos para
    definir o comportamento específico de scraping.
    
    Args:
        nome_buscador: Identificador único para a instância do scraper.
        debug: Se True, ativa logs de depuração e mantém arquivos baixados.
    
    Atributos:
        session: Instância de requests.Session para fazer requisições HTTP.
        api_base: URL base da API ou site a ser raspado.
        download_path: Diretório onde os arquivos baixados serão armazenados.
        sleep_time: Atraso entre requisições em segundos.
        type: Tipo do arquivo de dados baixados ('json', 'html', etc.).
        query_page_name: Nome do parâmetro de consulta usado para paginação.
        query_page_multiplier: Multiplicador para números de página na paginação.
        query_page_increment: Valor a ser adicionado aos números de página.
        debug: Flag para modo de depuração.
        timeout: Tupla (connect_timeout, read_timeout) para requisições.
        api_method: Método HTTP a ser usado nas requisições ('GET' ou 'POST').
        old_page_name: Nome do parâmetro para a página anterior.
    """
    
    def __init__(self, nome_buscador: str, debug: bool = True):
        """Inicializa o BaseScraper com configuração comum."""
        self.nome_buscador: str = nome_buscador
        self.download_path: str = tempfile.mkdtemp()
        self.session: requests.Session = requests.Session()
        self.sleep_time: int = 2
        self.query_page_multiplier: int = 1
        self.query_page_increment: int = 0
        self.debug: bool = debug
        self.timeout: tuple[int, int] = (10, 30)
        self.old_page_name: str | None = None
        self.exclude_cols_from_dedup: list[str] = []
        self.session.headers.update({
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt-BR,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
        })
        self.max_retries: int = 3

        self._api_base: str # Deve ser definido pela subclasse
        self._type: Literal['JSON', 'HTML'] # Deve ser definido pela subclasse
        self._query_page_name: str # Deve ser definido pela subclasse
        self._api_method: Literal['GET', 'POST']

        self._start_logger()

    @property
    @abstractmethod
    def api_base(self) -> str:
        ...

    @property
    @abstractmethod
    def type(self) -> Literal['JSON', 'HTML']:
        ...

    @property
    @abstractmethod
    def query_page_name(self) -> str:
        ...

    @property
    @abstractmethod
    def api_method(self) -> Literal['GET', 'POST']:
        ...

    def _start_logger(self):
        # Configuração do logger
        self.logger = logging.getLogger(self.nome_buscador)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)

    def scrape(self, **kwargs) -> pl.DataFrame:
        """Método principal para executar o processo de scraping.
        
        Args:
            **kwargs: Parâmetros de busca para o scraper. Se algum parâmetro for
                uma lista/tupla, o scraper processará cada valor na sequência.
                O parâmetro especial 'paginas' pode ser um objeto range para
                especificar as páginas.
    
        Returns:
            pl.DataFrame: DataFrame combinado com todos os dados raspados.
            
        Raises:
            ValueError: Se múltiplos parâmetros forem fornecidos como listas/tuplas.
        """
        
        # TODO: Revisar a lógica
        self.logger.info(f"Iniciando scrape com parâmetros {kwargs}")
        # Suporte a lista de valores de busca
        list_keys = [k for k, v in kwargs.items() if isinstance(v, (list, tuple)) and k != "paginas"]
        if list_keys:
            if len(list_keys) > 1:
                raise ValueError("Scrape só suporta lista de valores de busca para um parâmetro")
            key = list_keys[0]
            static_kwargs = {k: v for k, v in kwargs.items() if k != key}
            dfs: list[pl.DataFrame] = []
            for val in kwargs[key]:
                self.logger.info(f"Iniciando scrape para {key}={val}")
                loop_kwargs = {**static_kwargs, key: val}
                path_result = self._download_data(**loop_kwargs)
                df = self._parse_data(path_result)
                
                termo_busca_val = str(val)
                df = df.with_columns(pl.lit(termo_busca_val).alias("termo_busca"))
                self.logger.debug(f"Adicionada coluna termo_busca={termo_busca_val} aos resultados")
                
                dfs.append(df)
                if self.debug is False:
                    shutil.rmtree(path_result)
            result = pl.concat(dfs) if dfs else pl.DataFrame()
            
            result = self._remove_duplicates(result)
                
            return result
        # Fallback para busca única
        else:
            path_result = self._download_data(**kwargs)
            result = self._parse_data(path_result)

            # Determina qual parâmetro contém o termo de busca
            termo_param = next((k for k in kwargs if k in ['pesquisa', 'termo', 'q', 'query']), None)
            if termo_param:
                termo_busca = str(kwargs[termo_param])
                result = result.with_columns(pl.lit(termo_busca).alias("termo_busca"))
                self.logger.debug(f"Adicionada coluna termo_busca={termo_busca} aos resultados")
            
            self.logger.info(f"Scrape finalizado, limpando diretório {path_result}")
            if self.debug is False:
                shutil.rmtree(path_result)
            
            result = self._remove_duplicates(result)
            
            return result

    def _download_data(self, **kwargs) -> str:
        self.logger.debug(f"Definindo consulta")
        query_base = self._set_query_base(**kwargs)
        self.logger.debug(query_base)
        
        self.logger.debug(f"Definindo n_pags")
        n_pags = self._get_n_pags(query_base)

        self.logger.debug(f"Definindo paginas")
        paginas = kwargs.get("paginas")
        paginas = self._set_paginas(paginas, n_pags)

        # Verificação de sanidade - certifique-se de que paginas é iterável
        if not hasattr(paginas, '__iter__'):
            self.logger.error(f"paginas não é iterável: {paginas}")
            paginas = range(0) # range vazio como fallback

        download_dir = self._create_download_dir()      

        # Força a conversão para lista para garantir que tqdm funcione corretamente
        total_pages = list(paginas)
        
        for pag in tqdm(total_pages, desc="Baixando documentos"):
            time.sleep(self.sleep_time)
            self.logger.debug(f"Baixando página {pag}")

            query_atual = self._set_query_atual(query_base, pag)
            self.logger.debug(query_atual)

            try:
                r = self._set_r(query_atual)
                self.logger.debug(f"Response status: {r.status_code}")
                
                # Se erro de servidor, registra e pula esta página
                if r.status_code >= 500:
                    self.logger.warning(f"Server error {r.status_code} para URL {r.url}, ignorando página {pag}")
                    continue

                file_name = f"{download_dir}/{self.nome_buscador}_{pag:05d}.{self.type.lower()}"
                
                with open(file_name, "w", encoding="utf-8") as f:
                    # Write response content: use text or JSON dump fallback
                    content = r.text if r.text and r.text.strip() else json.dumps(r.json(), ensure_ascii=False)
                    f.write(content)
                self.logger.debug(f"Arquivo salvo: {file_name}")
                
            except Exception as e:
                self.logger.error(f"Erro ao baixar página {pag}: {e}")
                continue

        return download_dir

    def _get_n_pags(self, query_inicial):
        """
        Tenta obter o número total de páginas para uma consulta.

        Faz uma requisição para a URL com a query_inicial e extrai o número
        total de páginas do conteúdo da resposta. Se ocorrer um erro de servidor
        (status code 500 ou maior), registra e tenta novamente em 2, 4, 8, ...
        segundos até atingir o limite de tentativas.

        Args:
            query_inicial: Dicionário com a query a ser enviada para a API.

        Returns:
            int: Número total de páginas encontradas para a consulta.
        """
        # Inicializa a variável de retorno com None para que possa ser detectado
        # um erro de servidor e não um erro de extração de conteúdo
        contagem = None
        
        for attempt in range(self.max_retries):
            self.logger.debug(f"Enviando r0 (tentativa {attempt + 1}/{self.max_retries})")
            
            r0 = self._set_r(query_inicial)
            self.logger.debug(r0)

            if r0.status_code < 500:
                break
            
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                self.logger.warning(f"Erro do servidor {r0.status_code}, tentando novamente em {wait_time}s")
                time.sleep(wait_time)

        self.logger.debug(f"Encontrando n_pags")
        contagem = self._find_n_pags(r0)

        if contagem is None:
            self.logger.error(f"Erro ao extrair n_pags: {r0.text}")
        
        self.logger.debug(f"Encontradas {contagem} páginas para consulta {query_inicial}")
        return contagem

    def _set_paginas(self, paginas, n_pags):
        # TODO: repensar essa escolha
        if n_pags is None:
            self.logger.warning("n_pags é None, definindo como 0")
            n_pags = 0
        
        # Se não especificado, pega todas as páginas
        if paginas is None:
            paginas = range(1, n_pags + 1)
        else:
            start, stop, step = paginas.start, min(paginas.stop, n_pags + 1), paginas.step
            paginas = range(start, stop, step)
        return paginas

    def _set_query_atual(self, query_real, pag) -> dict[str, str]:
        query_atual = query_real
        
        query_atual[self.query_page_name] = pag * self.query_page_multiplier + self.query_page_increment
        
        if self.old_page_name is not None:
            query_atual[self.old_page_name] = query_atual[self.query_page_name] - 1
        
        return query_atual

    def _set_r(self, query_atual):
        if self.api_method == 'POST':
            r = self.session.post(
                self.api_base, 
                data=query_atual,
                timeout=self.timeout
            )
        elif self.api_method == 'GET':
            r = self.session.get(
                self.api_base, 
                params=query_atual, 
                timeout=self.timeout
            )
        else:
            raise ValueError(f"Método de API inválido: {self.api_method}")
        
        return r

    @abstractmethod
    def _set_query_base(self, **kwargs) -> dict[str, Any]:
        """Cria os parâmetros base para a requisição à API.
        
        Este método deve ser implementado pelas subclasses para definir como
        construir os parâmetros iniciais da consulta com base nos argumentos
        fornecidos.
        
        Args:
            **kwargs: Parâmetros de busca passados para o método scrape().
            
        Returns:
            dict: Parâmetros de consulta para a requisição inicial à API.
        """
        ...

    @abstractmethod
    def _find_n_pags(self, response: requests.Response) -> int:
        """Determina o número total de páginas a serem raspadas.
        
        Este método deve ser implementado pelas subclasses para analisar a resposta
        inicial e determinar quantas páginas de dados estão disponíveis.
        
        Args:
            response: A resposta inicial da API ou website.
            
        Returns:
            int: Número total de páginas a serem raspadas.
        """
        ...
        
    def _parse_data(self, path: str) -> pl.DataFrame:
        """Analisa os dados de um arquivo ou diretório e os consolida em um DataFrame.

        Se 'path' for um arquivo, ele será processado diretamente. Se for um diretório,
        todos os arquivos correspondentes a 'self.type' dentro do diretório (recursivamente)
        serão processados.

        Args:
            path: Caminho para o arquivo ou diretório contendo os dados a serem analisados.

        Returns:
            pl.DataFrame: DataFrame consolidado com todos os dados analisados.
        """
        self.logger.debug(f"Analisando dados de: {path}")
        
        result = []
        arquivos = glob.glob(f"{path}/**/*.{self.type}", recursive=True)
        arquivos = [f for f in arquivos if os.path.isfile(f)]

        for file in tqdm(arquivos, desc="Processando documentos"):
            try:
                single_result = self._parse_page(file)
            except Exception as e:
                self.logger.error(f"Erro ao processar {file}: {e}")
                single_result = None
                continue

            if single_result is not None:
                result.append(single_result)
        
        if not result:
            return pl.DataFrame()
        
        return pl.concat(result)

    @abstractmethod
    def _parse_page(self, path: str) -> pl.DataFrame:
        """Analisa uma única página de dados baixados.
        
        Este método deve ser implementado pelas subclasses para definir como
        converter os dados baixados em um DataFrame do polars.
        
        Args:
            path: Caminho para o arquivo baixado a ser analisado.
            
        Returns:
            pl.DataFrame: Dados analisados como um DataFrame.
        """
        ...

    def _remove_duplicates(self, df: pl.DataFrame) -> pl.DataFrame:
        """Remove duplicatas do DataFrame e agrupa os termos de busca.
        
        Este método utiliza a função utilitária remove_duplicates() para eliminar
        linhas duplicadas, considerando as colunas definidas em exclude_cols_from_dedup.
        
        Args:
            df: DataFrame a ser processado.
            
        Returns:
            pl.DataFrame: DataFrame sem duplicatas e com termos de busca agrupados.
        """
        self.logger.debug(f"Removendo duplicatas usando exclude_cols: {self.exclude_cols_from_dedup}")
        
        # Chama a função utilitária standalone
        return remove_duplicates(df, self.exclude_cols_from_dedup)
    
    def _create_download_dir(self) -> str:
        """Cria um diretório para armazenar os arquivos baixados.
        
        Gera um caminho único usando um timestamp para garantir que cada
        sessão de scraping tenha seu próprio diretório.
        
        Returns:
            str: Caminho do diretório criado.
        """
        # Chama a função utilitária standalone
        path = create_download_dir(self.download_path, self.nome_buscador)
        self.logger.debug(f"Criado diretório de download em {path}")
        
        return path