from .base_scraper import BaseScraper
from typing import Any
import polars as pl
import tempfile
import requests

class ScraperPresidencia(BaseScraper):
    def __init__(self, download_path = None): # sleep_time = 0.5 causa aviso de "Too Many Requests"
        super().__init__("PRESIDENCIA")
        self.api_base = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao'
        self._set_download_path(download_path)
        self.type = 'json'

    def _set_queries(self, **kwargs) -> tuple[dict[str, Any], dict[str, Any]]:
        ...

    def _find_n_pags(self, r0) -> int:
        ...

    def _parse_page(self, path) -> pl.DataFrame:
        ...

    def _set_query_atual(self, query_real, pag) -> dict[str, Any]:
        ...