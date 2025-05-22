from typing import Any

import polars as pl
import requests

from .base_scraper import BaseScraper

class ScraperNOME(BaseScraper):
    def __init__(self, download_path = None):
        super().__init__("<NOME>")
        self.api_base = '<url>'
        self._set_download_path(download_path)
        self.type = '<preencher>'
        self.query_page_name = ''

    def _set_query_base(self, **kwargs) -> dict[str, Any]:
        ...

    def _find_n_pags(self, r0) -> int:
        ...

    def _parse_page(self, path) -> pl.DataFrame:
        ...