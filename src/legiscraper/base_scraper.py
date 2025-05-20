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
import glob

class BaseScraper(ABC):
    def __init__(self, nome_buscador: str):
        self.nome_buscador: str = nome_buscador
        self.session: requests.Session = requests.Session()
        self.api_base: str
        self.download_path: str | None = None
        self.sleep_time: int = 2
        self.type: str

    def _set_download_path(self, path: str | None = None):
        if path is None:
            path = tempfile.mkdtemp()
        self.download_path = path

    def scrape(self, **kwargs):
        path_result = self.download_data(**kwargs) # , classe, assunto, comarca, id_processo,
        data_parsed = self.parse_data(path_result)
        shutil.rmtree(path_result)
        return data_parsed
    
    def download_data(
        self, 
        **kwargs
    ):
        query_inicial, query_real = self._set_query(**kwargs)
        n_pags = self._get_n_pags(query_inicial)

        paginas = kwargs.get('paginas')
        self._set_paginas(paginas, n_pags)

        download_dir  = self._create_download_dir()

        for pag in tqdm(paginas, desc="Baixando documentos"):
            time.sleep(self.sleep_time)

            query_atual = self._set_query_atual(query_real, pag)
                      
            r = self.session.get(self.api_base, params=query_atual)

            file_name = self._set_file_name(download_dir, pag)

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(r.text)
        
        return download_dir

    def _config(self):
        if not self.api_base:
            raise ValueError("api_base não definido")
        if not self.download_path:
            self._set_download_path()
        assert self.download_path is not None

    def _get_n_pags(self, query_inicial):
        r0 = self.session.get(
            self.api_base,
            params=query_inicial
        )
        contagem = self._find_n_pags(r0)

        return contagem
    
    def _set_paginas(self, paginas, n_pags):
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

        return path

    def _set_file_name(self, download_dir, pag):
        file_name = f"{download_dir}/{self.nome_buscador}_{pag:05d}.{self.type}"

        return file_name
    
    @abstractmethod
    def _set_query(self, **kwargs) -> dict[str, Any]: 
        ...

    @abstractmethod
    def _find_n_pags(self, r0) -> int:
        ...

    @abstractmethod
    def _set_query_atual(self, query_real, pag) -> dict[str, Any]:
        ...

    def parse_data(self, path: str) -> pl.DataFrame:
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
                    print(f"Error processing {file}: {e}")
                    single_result = None
                    continue
                if single_result is not None:
                    result.append(single_result)
        if not result:
            return pl.DataFrame()
        return pl.concat(result)
    
    @abstractmethod
    def _parse_page(self, path) -> pl.DataFrame:
        ...
