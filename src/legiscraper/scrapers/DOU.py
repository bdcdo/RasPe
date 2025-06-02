from typing import Any
import polars as pl
import requests
import re

from ..base_scraper import BaseScraper, HTMLScraper

class ScraperDOU(BaseScraper, HTMLScraper):
    def __init__(self, id: str, displayDate: str, download_path = None):
        super().__init__("DOU")
        self.api_base = "https://www.in.gov.br/consulta/-/buscar/dou"
        self._set_download_path(download_path)
        self.type = 'html'
        self.query_page_name = 'newPage'
        self.query_page_multiplier = 1
        self.query_page_increment = 0
        self.api_method = 'GET'
        self.id = id
        self.displayDate = displayDate
        self.session.headers.update({"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0"
        })

    def _set_query_base(self, **kwargs) -> dict[str, Any]:
        pesquisa = kwargs.get('pesquisa')

        self._config()
        
        return {
            "q": pesquisa,
            "s": "todos",
            "exactDate": "all",
            "sortType": "0",
            "delta": "20",
            "currentPage": "1",
            "newPage": 1,
            "score": "0",
            "id": self.id,
            "displayDate": self.displayDate,
        }

    def _find_n_pags(self, r0) -> int:
        if r0.status_code >= 500:
            self.logger.warning(f"Server error {r0.status_code} for URL {r0.url}, returning 0 pages")
            return 0
        
        num = 0
        r0.raise_for_status()

        r0s = self.soup_it(r0.content)
        p_tag = r0s.find('p', class_='search-total-label text-default').text
        
        if p_tag:
            self.logger.debug(f"Found p tag text: '{p_tag}'")
            match = re.search(r'(\d+)\s+resultados', p_tag)
            if match:
                num = int(match.group(1))

        self.logger.debug(f"Extracted number of results: {num}")
        
        # Convert results to pages (assuming 20 results per page)
        pages = (num + 19) // 20  # Round up division
        self.logger.debug(f"Calculated pages: {pages}")
        return pages                

    def _parse_page(self, path) -> pl.DataFrame:
        ...