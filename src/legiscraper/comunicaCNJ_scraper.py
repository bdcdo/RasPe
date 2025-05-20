from .base_scraper import BaseScraper
import polars as pl
import json

class comunicaCNJ_Scraper(BaseScraper):
    """Raspador para o site de Comunicações Processuais do Conselho Nacional de Justiça."""

    def __init__(self, download_path = None):
        super().__init__("CNJ")
        self.api_base = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao'
        self._set_download_path(download_path)
        self.type = 'json'
    
    def _set_queries(self, **kwargs):
        pesquisa = kwargs.get('pesquisa')
        data_inicio = kwargs.get('data_inicio')
        data_fim = kwargs.get('data_fim')        

        self._config()
        
        query_inicial = {
                'itensPorPagina': 5,
                'texto': pesquisa,
                'dataDisponibilizacaoInicio': data_inicio
            }
        
        query_real = query_inicial
        
        if data_fim:
                query_real['dataDisponibilizacaoFim'] = data_fim

        return query_inicial, query_real
        
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