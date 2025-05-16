from .base_scraper import BaseScraper
import tempfile
import requests

class ScraperPresidencia(BaseScraper):
    def __init__(self, verbose = 1, download_path = None, sleep_time = 2, **kwargs): # sleep_time = 0.5 causa aviso de "Too Many Requests"
        super().__init__("PRESIDENCIA")
        self.api_base = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao'
        self.set_download_path(download_path)
        self.sleep_time = sleep_time

    def get_query_params(self, **kwargs) -> dict:
        return {
            "termo": 
        }

