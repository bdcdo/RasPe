from typing import Any

import polars as pl
import requests

from ..base_scraper import BaseScraper

class ScraperFolha(BaseScraper):
    def __init__(self, download_path = None):
        super().__init__("FOLHA")
        self.api_base = '"https://search.folha.uol.com.br/search"'
        self._set_download_path(download_path)
        self.type = 'HTML'
        self.query_page_name = 'sr'
        self.query_page_multiplier = 25
        self.query_page_increment = 1
        self.api_method = 'GET'

        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt-BR,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive",
            "DNT": "1",
            "Priority": "u=0, i",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "TE": "trailers",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0"
        })

    def _set_query_base(self, **kwargs) -> dict[str, Any]:
        querystring = {"q":"gilmar mendes","site":"todos","sd":"01/01/2015","ed":"29/05/2025","periodo":"personalizado","sr":"26"}
        payload = ""
        response = requests.request("GET", url=self.api_base, data=payload, params=querystring)
        ...

    def _find_n_pags(self, r0) -> int:
        ...

    def _parse_page(self, path) -> pl.DataFrame:
        ...