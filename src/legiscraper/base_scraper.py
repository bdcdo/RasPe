from abc import ABC, abstractmethod
import requests
import tempfile
import os

class BaseScraper(ABC):
    def __init__(self, nome_buscador: str):
        self.nome_buscador: str = nome_buscador
        self.session: requests.Session = requests.Session()
        self.api_base: str | None = None
        self.download_path: str | None = None

    def set_download_path(self, path: str | None = None):
        if path is None:
            path = tempfile.mkdtemp()
        self.download_path = path

    @abstractmethod
    def get_query_params(self) -> dict:
        """
        Deve retornar um dict de parâmetros de query para a requisição.
        Implementado em cada subclasse.
        """
        ...
        

    def download(self, filename: str, **kwargs) -> str:
        if not self.api_base:
            raise ValueError("api_base não definido")
        if not self.download_path:
            self.set_download_path()
        assert self.download_path is not None

        params = self.get_query_params(**kwargs)
        response = self.session.get(self.api_base, params=params)
        response.raise_for_status()

        fullpath = os.path.join(self.download_path, filename)
        with open(fullpath, "wb") as f:
            f.write(response.content)

        return fullpath
