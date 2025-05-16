from .scraper_presidencia import ScraperPresidencia

def scraper(nome_buscador: str, **kwargs):
    """Retorna o raspador correspondente ao tribunal solicitado."""
    nome_buscador = nome_buscador.upper()
    
    if nome_buscador == "PRESIDENCIA":
        return ScraperPresidencia(**kwargs)
    else:
        raise ValueError(f"Buscador '{nome_buscador}' ainda não é suportado.")