from .scrapers.senado import ScraperSenadoFederal
from .scrapers.presidencia import ScraperPresidencia
from .scrapers.comunicaCNJ import comunicaCNJ_Scraper
from .scrapers.ipea import IpeaScraper
from .base_scraper import BaseScraper
from typing import Type

def scraper(nome_buscador: str, **kwargs) -> BaseScraper:
    """Retorna o raspador correspondente ao tribunal solicitado."""
    
    nome = nome_buscador.upper()
    mapping: dict[str, Type[BaseScraper]] = {
        "PRESIDENCIA": ScraperPresidencia,
        "CNJ": comunicaCNJ_Scraper,
        "IPEA": IpeaScraper,
        "SENADO": ScraperSenadoFederal
    }

    try:
        klas = mapping[nome]
    except KeyError:
        raise ValueError(f"Buscador '{nome}' ainda não é suportado.")
        
    return klas(**kwargs)