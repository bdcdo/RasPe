"""Tests for the scraper manager functionality."""
import pytest

from src.legiscraper.scraper_manager import scraper

def test_scraper_factory():
    """Test the scraper factory function with different scraper types."""
    # Test CNJ scraper creation
    cnj = scraper("CNJ")
    assert cnj is not None
    assert cnj.nome_buscador == "CNJ"
    assert "comunicaapi.pje.jus.br" in cnj.api_base

    # Test Presidência scraper creation
    pres = scraper("PRESIDENCIA")
    assert pres is not None
    assert pres.nome_buscador == "PRESIDENCIA"
    assert "legislacao.presidencia.gov.br" in pres.api_base

    # Test passing kwargs to scraper
    cnj_with_path = scraper("CNJ", download_path="/tmp/test")
    assert cnj_with_path.download_path == "/tmp/test"

    # Test DOU scraper creation
    dou = scraper("DOU", id="1", displayDate="2025-06-02")
    assert dou is not None
    assert dou.nome_buscador == "DOU"
    assert "in.gov.br" in dou.api_base
    
    # Test Folha scraper creation
    folha = scraper("FOLHA")
    assert folha is not None
    assert folha.nome_buscador == "FOLHA"
    assert "folha.uol.com.br" in folha.api_base

def test_scraper_factory_unsupported():
    """Test that an unsupported scraper raises a ValueError."""
    with pytest.raises(ValueError) as excinfo:
        scraper("UNSUPPORTED_SCRAPER")
    
    assert "não é suportado" in str(excinfo.value)

def test_scraper_case_insensitive():
    """Test that scraper names are case-insensitive."""
    # Test different case variations
    scraper1 = scraper("cnj")
    scraper2 = scraper("Cnj")
    scraper3 = scraper("CNJ")
    
    assert scraper1.nome_buscador == "CNJ"
    assert scraper2.nome_buscador == "CNJ"
    assert scraper3.nome_buscador == "CNJ"
