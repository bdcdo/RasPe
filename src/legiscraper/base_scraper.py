"""
Módulo base para funcionalidades de web scraping.

Este módulo fornece a classe base abstrata BaseScraper que serve como fundamento
para construção de web scrapers. Gerencia tarefas comuns como gerenciamento de
sessão, paginação, tentativas de requisição e operações de arquivo.

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
from typing import Any
from datetime import datetime
from tqdm import tqdm
import polars as pl
import requests
import tempfile
import os
import shutil
import time
import logging
import glob
import json

class BaseScraper(ABC):
    """Classe base para criação de web scrapers.
    
    Fornece funcionalidades comuns para tarefas de web scraping, incluindo
    gerenciamento de sessão, paginação, tentativas de requisição e operações
    de arquivo. As subclasses devem implementar os métodos abstratos para definir
    o comportamento específico de scraping.
    
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
        old_page: Se deve incluir o número da página anterior nas requisições.
        old_page_name: Nome do parâmetro para a página anterior.
    """
    
    def __init__(self, nome_buscador: str, debug: bool = True):
        """Inicializa o BaseScraper com configuração comum."""
        self.nome_buscador: str = nome_buscador
        self.session: requests.Session = requests.Session()
        self.api_base: str = ""  # Deve ser definido pela subclasse
        self.download_path: str | None = None
        self.sleep_time: int = 2
        self.type: str = ""  # Deve ser definido pela subclasse
        self.query_page_name: str = "page"  # Nome padrão do parâmetro de página
        self.query_page_multiplier: int = 1
        self.query_page_increment: int = 0
        self.debug: bool = debug
        self.timeout: tuple[int, int] = (10, 30)
        self.api_method: str = 'GET'
        self.old_page: bool = False
        self.old_page_name: str = 'currentPage'
        self.exclude_cols_from_dedup: list[str] = []  # Colunas a excluir na remoção de duplicatas

        self.session.headers.update({
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt-BR,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
        })

        # Configuração do logger
        self.logger = logging.getLogger(self.nome_buscador)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)

    def _set_download_path(self, path: str | None = None) -> None:
        """Defines the directory for downloading scraped files.
        
        Args:
            path: Path to the directory to store the files. If None,
                a temporary directory will be created.
        """
        if path is None:
            path = tempfile.mkdtemp()
        else:
            os.makedirs(path, exist_ok=True)
        self.download_path = path
        self.logger.debug(f"Download path set to {self.download_path}")

    def scrape(self, **kwargs) -> pl.DataFrame:
        """Método principal para executar o processo de scraping.
        
        Args:
            **kwargs: Parâmetros de busca para o scraper. Se algum parâmetro for
                uma lista/tupla, o scraper processará cada valor na sequência.
                O parâmetro especial 'paginas' pode ser um objeto range para
                especificar as páginas.
                O parâmetro especial 'rastrear_termo_busca' (bool) controla se
                uma coluna com o termo de busca será adicionada (padrão: True).
    
        Returns:
            pl.DataFrame: DataFrame combinado com todos os dados raspados.
            
        Raises:
            ValueError: Se múltiplos parâmetros forem fornecidos como listas/tuplas.
        """
        # Extrai e remove parâmetros especiais
        rastrear_termo_busca = kwargs.pop('rastrear_termo_busca', True)
        
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
                path_result = self.download_data(**loop_kwargs)
                df = self.parse_data(path_result)
                
                # Adiciona a coluna com o termo de busca se solicitado
                if rastrear_termo_busca and not df.is_empty():
                    termo_busca_val = str(val)
                    df = df.with_columns(pl.lit(termo_busca_val).alias("termo_busca"))
                    self.logger.debug(f"Adicionada coluna termo_busca={termo_busca_val} aos resultados")
                
                dfs.append(df)
                if self.debug is False:
                    shutil.rmtree(path_result)
            result = pl.concat(dfs) if dfs else pl.DataFrame()
            
            # Remover duplicatas e agrupar termos de busca se há dados
            if not result.is_empty() and rastrear_termo_busca:
                result = self._remove_duplicates(result)
                
            return result
        # Fallback para busca única
        else:
            path_result = self.download_data(**kwargs)
            result = self.parse_data(path_result)
            
            # Adiciona o termo de busca para busca única, se solicitado
            if rastrear_termo_busca and not result.is_empty():
                # Determina qual parâmetro contém o termo de busca
                termo_param = next((k for k in kwargs if k in ['pesquisa', 'termo', 'q', 'query']), None)
                if termo_param:
                    termo_busca = str(kwargs[termo_param])
                    result = result.with_columns(pl.lit(termo_busca).alias("termo_busca"))
                    self.logger.debug(f"Adicionada coluna termo_busca={termo_busca} aos resultados")
            
            self.logger.info(f"Scrape finalizado, limpando diretório {path_result}")
            if self.debug is False:
                shutil.rmtree(path_result)
            
            # Remover duplicatas apenas se houver dados
            if not result.is_empty() and rastrear_termo_busca:
                result = self._remove_duplicates(result)
            
            return result

    def download_data(self, **kwargs):
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

                # Salva conteúdo da página
                file_name = self._set_file_name(download_dir, pag)
                with open(file_name, "w", encoding="utf-8") as f:
                    # Write response content: use text or JSON dump fallback
                    content = r.text if r.text and r.text.strip() else json.dumps(r.json(), ensure_ascii=False)
                    f.write(content)
                self.logger.debug(f"Arquivo salvo: {file_name}")
                
            except Exception as e:
                self.logger.error(f"Erro ao baixar página {pag}: {e}")
                continue

        return download_dir

    def _config(self):
        if not self.api_base:
            raise ValueError("api_base não definido")
        if not self.download_path:
            self._set_download_path()
        assert self.download_path is not None

    def _get_n_pags(self, query_inicial):
        max_retries = 3
        for attempt in range(max_retries):
            self.logger.debug(f"Enviando r0 (tentativa {attempt + 1}/{max_retries})")
            
            r0 = self._set_r(query_inicial)
            self.logger.debug(r0)


            if r0.status_code < 500:
                break
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                self.logger.warning(f"Erro do servidor {r0.status_code}, tentando novamente em {wait_time}s")
                time.sleep(wait_time)

        self.logger.debug(f"Encontrando n_pags")
        contagem = self._find_n_pags(r0)

        self.logger.debug(f"Encontradas {contagem} páginas para consulta {query_inicial}")
        return contagem

    def _set_paginas(self, paginas, n_pags):
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

    def _create_download_dir(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        path = f"{self.download_path}/{self.nome_buscador}/{timestamp}"
        if not os.path.isdir(path):
            os.makedirs(path)
            self.logger.debug(f"Criado diretório de download em {path}")
        return path

    def _set_file_name(self, download_dir, pag):
        file_name = f"{download_dir}/{self.nome_buscador}_{pag:05d}.{self.type}"
        return file_name

    def _set_query_atual(self, query_real, pag) -> dict[str, str]:
        query_atual = query_real
        query_atual[self.query_page_name] = pag * self.query_page_multiplier + self.query_page_increment
        if self.old_page:
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

    def _remove_duplicates(self, df: pl.DataFrame) -> pl.DataFrame:
        """Remove duplicatas do DataFrame e agrupa os termos de busca.
        
        Este método remove linhas duplicadas no DataFrame, excluindo as colunas
        especificadas em exclude_cols e a coluna 'termo_busca'. Para registros
        que são duplicados, os valores da coluna 'termo_busca' são agrupados em uma lista.
        
        Args:
            df: DataFrame a ser processado.
            exclude_cols: Lista adicional de colunas para excluir ao detectar duplicatas.
            
        Returns:
            pl.DataFrame: DataFrame sem duplicatas e com termos de busca agrupados.
        """
        self.logger.debug(f"Removendo duplicatas. Colunas excluídas: {self.exclude_cols_from_dedup}")
        
        # Verificar se há coluna termo_busca
        if "termo_busca" not in df.columns:
            self.logger.debug("Coluna termo_busca não encontrada, retornando DataFrame original")
            return df
        
        # Preparar lista de colunas para deduplicação
        all_exclude_cols = ["termo_busca", *self.exclude_cols_from_dedup]
        dedup_cols = [col for col in df.columns if col not in all_exclude_cols]
        
        if not dedup_cols:
            self.logger.debug("Nenhuma coluna disponível para deduplicação")
            return df
        
        # Verificar se há duplicatas
        dedup_counts = df.group_by(dedup_cols).count()
        n_duplicates = dedup_counts.filter(pl.col("count") > 1).height
        
        if n_duplicates == 0:
            self.logger.debug("Nenhuma duplicata encontrada")
            return df
        
        self.logger.info(f"Encontradas {n_duplicates} entradas duplicadas")
        
        # Agrupar termos de busca para duplicatas
        agregado = df.group_by(dedup_cols).agg(
            pl.col("termo_busca").alias("termo_busca_list"),
            *[pl.col(col).first().alias(col) for col in self.exclude_cols_from_dedup]
        )
        
        # Converter a coluna de termos para o formato apropriado
        result = agregado.with_columns([
            pl.when(pl.col("termo_busca_list").list.len() > 1)
              .then(pl.col("termo_busca_list").list.join(", "))
              .otherwise(pl.col("termo_busca_list").list.first())
              .alias("termo_busca")
        ]).drop("termo_busca_list")
        
        self.logger.info(f"Remoção de duplicatas concluída. Linhas reduzidas de {df.height} para {result.height}")
        return result
        
    def parse_data(self, path: str) -> pl.DataFrame:
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
        
        if os.path.isfile(path):
            result = [self._parse_page(path)]
        else:
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
        
        # Verifica se todos os DataFrames têm o mesmo esquema antes de concatenar
        if len(result) > 1:
            first_schema = result[0].schema
            for i, df in enumerate(result[1:], 1):
                if df.schema != first_schema:
                    self.logger.warning(f"Diferença de esquema: DataFrame {i} tem {len(df.columns)} colunas {list(df.columns)}, esperado {len(first_schema)} colunas {list(first_schema.keys())}")
        
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

class HTMLScraper:
    """Classe mixin para scrapers que precisam analisar conteúdo HTML."""
    
    def soup_it(self, content: str | bytes) -> 'BeautifulSoup':
        """Analisa conteúdo HTML usando BeautifulSoup.
        
        Args:
            content: Conteúdo HTML para análise, como string ou bytes.
            
        Returns:
            BeautifulSoup: Documento HTML analisado.
            
        Note:
            Requer o pacote 'beautifulsoup4' instalado.
        """
        from bs4 import BeautifulSoup
        return BeautifulSoup(content, 'html.parser')
