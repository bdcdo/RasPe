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

class BaseScraper(ABC):
    def __init__(self, nome_buscador: str, debug: bool = True):
        self.nome_buscador: str = nome_buscador
        self.session: requests.Session = requests.Session()
        self.api_base: str
        self.download_path: str | None = None
        self.sleep_time: int = 2
        self.type: str
        self.query_page_name: str
        self.query_page_multiplier: int = 1
        self.query_page_increment: int = 0
        self.debug: bool = debug
        self.headers: dict = {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt-BR,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
        }
        self.timeout: tuple = (10, 30)
        self.api_method: str = 'get'

        # Logger setup
        self.logger = logging.getLogger(self.nome_buscador)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)

    def _set_headers(self, headers_scraper):
        self.headers.update(headers_scraper)
    
    def _set_download_path(self, path: str | None = None):
        if path is None:
            path = tempfile.mkdtemp()
        self.download_path = path
        self.logger.debug(f"Download path set to {self.download_path}")

    def scrape(self, **kwargs):
        self.logger.info(f"Starting scrape with parameters {kwargs}")
        path_result = self.download_data(**kwargs)  # , classe, assunto, comarca, id_processo,
        data_parsed = self.parse_data(path_result)
        self.logger.info(f"Scrape finished, cleaning up directory {path_result}")
        
        if self.debug is False:
            shutil.rmtree(path_result)

        return data_parsed

    def download_data(self, **kwargs):
        self.logger.debug(f"Setting query")
        query_base = self._set_query_base(**kwargs)
        self.logger.debug(query_base)
        
        self.logger.debug(f"Setting n_pags")
        n_pags = self._get_n_pags(query_base)

        self.logger.debug(f"Setting paginas")
        paginas = kwargs.get("paginas")
        paginas = self._set_paginas(paginas, n_pags)

        download_dir = self._create_download_dir()      

        for pag in tqdm(paginas, desc="Baixando documentos"):
            time.sleep(self.sleep_time)
            self.logger.debug(f"Downloading page {pag}")

            query_atual = self._set_query_atual(query_base, pag)
            self.logger.debug(query_atual)

            if self.api_method == 'post':
                r = self.session.post(
                    self.api_base, 
                    data=query_atual, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
            else:
                r = self.session.get(
                    self.api_base, 
                    params=query_atual, 
                    headers=self.headers, 
                    timeout=self.timeout
                )

            self.logger.debug(r)

            file_name = self._set_file_name(download_dir, pag)

            with open(file_name, "w", encoding="utf-8") as f:
                f.write(r.text)

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
            self.logger.debug(f"Sending r0 (attempt {attempt + 1}/{max_retries})")
            
            if self.api_method == 'post':
                r0 = self.session.post(
                    self.api_base, 
                    data=query_inicial, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
            else:
                r0 = self.session.get(
                    self.api_base, 
                    params=query_inicial, 
                    headers=self.headers, 
                    timeout=self.timeout
                )

            if r0.status_code < 500:
                break
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                self.logger.warning(f"Server error {r0.status_code}, retrying in {wait_time}s")
                time.sleep(wait_time)

        self.logger.debug(f"Finding n_pags")
        contagem = self._find_n_pags(r0)

        self.logger.debug(f"Found {contagem} pages for query {query_inicial}")
        return contagem

    def _set_paginas(self, paginas, n_pags):
        if n_pags is None:
            self.logger.warning("n_pags is None, setting to 0")
            n_pags = 0
            
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
            self.logger.debug(f"Created download directory at {path}")
        return path

    def _set_file_name(self, download_dir, pag):
        file_name = f"{download_dir}/{self.nome_buscador}_{pag:05d}.{self.type}"
        return file_name

    def _set_query_atual(self, query_real, pag) -> dict[str, str]:
        query_atual = query_real
        query_atual[self.query_page_name] = pag * self.query_page_multiplier + self.query_page_increment
        return query_atual

    @abstractmethod
    def _set_query_base(self, **kwargs) -> dict[str, Any]:
        ...

    @abstractmethod
    def _find_n_pags(self, r0) -> int:
        ...

    def parse_data(self, path: str) -> pl.DataFrame:
        self.logger.debug(f"Parsing data")
        
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
                    self.logger.error(f"Error processing {file}: {e}")
                    single_result = None
                    continue
                if single_result is not None:
                    result.append(single_result)
        if not result:
            return pl.DataFrame()
        
        # Check if all DataFrames have the same schema before concatenating
        if len(result) > 1:
            first_schema = result[0].schema
            for i, df in enumerate(result[1:], 1):
                if df.schema != first_schema:
                    self.logger.warning(f"Schema mismatch: DataFrame {i} has {len(df.columns)} columns {list(df.columns)}, expected {len(first_schema)} columns {list(first_schema.keys())}")
        
        return pl.concat(result)

    @abstractmethod
    def _parse_page(self, path) -> pl.DataFrame:
        ...

class HTMLScraper(ABC):
    def soup_it(self, r0):
        from bs4 import BeautifulSoup as bs
        soup = bs(r0, 'html.parser')

        return soup
