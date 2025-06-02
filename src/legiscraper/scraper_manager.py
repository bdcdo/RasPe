from .scrapers.presidencia import ScraperPresidencia
from .scrapers.comunicaCNJ import comunicaCNJ_Scraper
from .scrapers.DOU import ScraperDOU
from .scrapers.Folha import ScraperFolha

def scraper(nome_buscador: str, **kwargs):
    """Retorna o raspador correspondente ao tribunal solicitado."""
    nome_buscador = nome_buscador.upper()
    
    if nome_buscador == "PRESIDENCIA":
        return ScraperPresidencia(**kwargs)
    elif nome_buscador == "CNJ":
        return comunicaCNJ_Scraper(**kwargs)
    elif nome_buscador == "DOU":
        return ScraperDOU(**kwargs)
    elif nome_buscador == "FOLHA":
        return ScraperFolha(**kwargs)
    else:
        raise ValueError(f"Buscador '{nome_buscador}' ainda não é suportado.")