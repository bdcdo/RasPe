from .base_scraper import BaseScraper
import polars as pl
import json
from typing import Any

class comunicaCNJ_Scraper(BaseScraper):
    """Raspador para o site de Comunicações Processuais do Conselho Nacional de Justiça."""

    def __init__(self, download_path = None):
        super().__init__("CNJ")
        self.api_base = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao'
        self.type = 'json'
        self.query_page_name = 'pagina'
        self._set_download_path(download_path)
    
    def _set_query(self, **kwargs):
        pesquisa = kwargs.get('pesquisa')
        data_inicio = kwargs.get('data_inicio')
        data_fim = kwargs.get('data_fim')        

        self._config()
        
        query_inicial = {
                'itensPorPagina': 5,
                'texto': pesquisa,
                'dataDisponibilizacaoInicio': data_inicio,
                'dataDisponibilizacaoFim': data_fim
            }

        return query_inicial
        
    def _find_n_pags(self, r0):
        contagem = r0.json()['count']
        return (contagem // 5) + 1        
    
    def _parse_page(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        lista_infos = []

        infos_processos = dados['items']

        for processo in infos_processos:
            lista_infos.append(processo)

        return pl.DataFrame(lista_infos)