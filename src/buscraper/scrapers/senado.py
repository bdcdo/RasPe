from ..base_scraper import BaseScraper
from ..html_scraper import HTMLScraper
from typing import Any, Literal
import pandas as pd
from bs4 import BeautifulSoup as bs
import tempfile
import requests
import re
import time

class ScraperSenadoFederal(BaseScraper, HTMLScraper):
    def __init__(self):
        super().__init__("SENADO")
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
            "DNT": "1",
            "Priority": "u=0, i",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
        })

        self._api_base = "https://wwwg.senado.leg.br/busca"
        self._type = 'HTML'
        self._query_page_name = 'p'
        self._api_method = 'GET'

    @property
    def api_base(self) -> str:
        return self._api_base

    @property
    def type(self) -> Literal['JSON'] | Literal['HTML']:
        return self._type

    @property
    def query_page_name(self) -> str:
        return self._query_page_name

    @property
    def api_method(self) -> Literal['GET'] | Literal['POST']:
        return self._api_method
    
    def _set_query_base(self, **kwargs) -> dict[str, Any]:
        pesquisa = kwargs.get('pesquisa')
        ano = kwargs.get('ano')
        tipo_materia = kwargs.get('tipo_materia')

        query_inicial = {
                'colecao': 'Legislação Federal',
                'tipo-materia':tipo_materia,
                'ano': ano,
                'q': pesquisa,
                'p': 1  
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
            a_tag = r0s.find('a', attrs={"data-click-type":"dynnav.colecao.Legislação Federal"})
            if a_tag:
                num_text = a_tag.text
                self.logger.debug(f"Found a text: '{num_text}'")

        num = int(num_text)

        self.logger.debug(f"Extracted number of results: {num}")
        
        # Convert results to pages (assuming 10 results per page)
        pages = (num + 9) // 10  # Round up division
        self.logger.debug(f"Calculated pages: {pages}")
        return pages

    def _parse_page(self, path) -> pd.DataFrame:
        from bs4 import BeautifulSoup
        
        columns = ['titulo', 'link_norma', 'link_detalhes', 'descricao', 'trecho_descricao']
        
        try:
            with open(path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            lista_infos = []

            soup = BeautifulSoup(html_content, 'html.parser')
                
            itens = soup.find('div', class_='col-xs-12 col-md-12 sf-busca-resultados').find_all('div', class_='sf-busca-resultados-item')

            for item in (itens):
                try:
                    titulo = item.find('h3').find('a').text.strip()
                    link_norma = item.find('h3').find_all('a')[0]['href']
                    link_detalhes = item.find('h3').find_all('a')[1]['href']
                    descricao = item.find('p').text.strip()
                    trecho_descricao = item.find_all('p')[2].text.strip()

                    lista_infos.append([titulo, link_norma, link_detalhes, descricao, trecho_descricao])
                except Exception as e:
                    self.logger.warning(f"Error parsing item in {path}: {e}")
                    continue

            return pd.DataFrame(lista_infos, columns=columns)
            
        except Exception as e:
            self.logger.error(f"Error parsing page {path}: {e}")
            return pd.DataFrame(columns=columns)