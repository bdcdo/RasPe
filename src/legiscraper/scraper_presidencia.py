from .base_scraper import BaseScraper, HTMLScraper
from typing import Any
import polars as pl
import tempfile
import requests
import re

class ScraperPresidencia(BaseScraper, HTMLScraper):
    def __init__(self, download_path = None): # sleep_time = 0.5 causa aviso de "Too Many Requests"
        super().__init__("PRESIDENCIA")
        self.api_base = "https://legislacao.presidencia.gov.br/pesquisa/ajax/resultado_pesquisa_legislacao.php"
        self._set_download_path(download_path)
        self.type = 'html'
        self.query_page_name = 'posicao'
        self.query_page_multiplier = 10
        self.query_page_increment = -10
        self.api_method = 'post'

    def _set_query_base(self, **kwargs) -> dict[str, Any]:
        pesquisa = kwargs.get('pesquisa')

        self._config()

        query_inicial = {
                'termo': pesquisa,
                'ordenacao': 'maior_data',
                'posicao': '0'
            }
        
        return query_inicial

    def _find_n_pags(self, r0) -> int:
        if r0.status_code >= 500:
            self.logger.warning(f"Server error {r0.status_code} for URL {r0.url}, returning 0 pages")
            return 0
        
        r0.raise_for_status()

        r0s = self.soup_it(r0.content)
        num_text = '0'
        if r0s:
            h4_tag = r0s.find('h4')
            if h4_tag:
                num_text = h4_tag.text
                self.logger.debug(f"Found h4 text: '{num_text}'")

        num = 0
        # Pattern specifically for "27 resultados encontrados"
        match = re.search(r'(\d+)\s+resultados?\s+encontrados?', num_text, re.IGNORECASE)
        if match:
            num = int(match.group(1))
        else:
            # Fallback to first number
            match = re.search(r'\d+', num_text)
            if match:
                num = int(match.group(0))

        self.logger.debug(f"Extracted number of results: {num}")
        
        # Convert results to pages (assuming 10 results per page)
        pages = (num + 9) // 10  # Round up division
        self.logger.debug(f"Calculated pages: {pages}")
        return pages

    def _parse_page(self, path) -> pl.DataFrame:
        ...