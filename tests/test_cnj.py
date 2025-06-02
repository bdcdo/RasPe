"""Tests for the CNJ scraper functionality."""
import pytest
import polars as pl
from unittest.mock import MagicMock
import json

from src.legiscraper.scraper_manager import scraper
from src.legiscraper.scrapers.comunicaCNJ import comunicaCNJ_Scraper

def test_cnj_scraper_creation():
    """Test that CNJ scraper can be created successfully."""
    # Test through the scraper factory
    cnj = scraper('CNJ')
    assert cnj is not None
    assert cnj.nome_buscador == "CNJ"
    assert "comunicaapi.pje.jus.br" in cnj.api_base

def test_cnj_scraper_initialization():
    """Test CNJ scraper initialization and default values."""
    cnj = comunicaCNJ_Scraper()
    
    assert cnj.nome_buscador == "CNJ"
    assert "comunicaapi.pje.jus.br" in cnj.api_base
    assert cnj.type == "json"
    assert cnj.api_method == "GET"
    assert "User-Agent" in cnj.session.headers

def test_cnj_set_query_base_default():
    """Test setting up the base query with default parameters."""
    cnj = comunicaCNJ_Scraper()
    query = cnj._set_query_base(pesquisa="teste")
    
    assert query["texto"] == "teste"
    assert query["itensPorPagina"] == 5
    assert "dataDisponibilizacaoInicio" not in query
    assert "dataDisponibilizacaoFim" not in query

def test_cnj_set_query_base_with_dates():
    """Test setting up the base query with date parameters."""
    cnj = comunicaCNJ_Scraper()
    query = cnj._set_query_base(
        pesquisa="teste",
        data_inicio="2023-01-01",
        data_fim="2023-12-31"
    )
    
    assert query["texto"] == "teste"
    assert query["dataDisponibilizacaoInicio"] == "2023-01-01"
    assert query["dataDisponibilizacaoFim"] == "2023-12-31"

def test_cnj_parse_response(tmp_path):
    """Test parsing the API response into a DataFrame."""
    cnj = comunicaCNJ_Scraper()
    response_data = {
        "total": 2,
        "itens": [
            {"id": 1, "texto": "Teste 1", "data": "2023-01-01"},
            {"id": 2, "texto": "Teste 2", "data": "2023-01-02"}
        ]
    }
    # Dump JSON to file and parse
    file = tmp_path / "page.json"
    file.write_text(json.dumps(response_data), encoding="utf-8")
    result_df = cnj._parse_page(str(file))
    assert isinstance(result_df, pl.DataFrame)
    assert result_df.shape == (2, 3)
    assert "id" in result_df.columns
    assert "texto" in result_df.columns
    assert "data" in result_df.columns
    assert result_df["id"].to_list() == [1, 2]

def test_cnj_scrape_basic(mock_requests, mock_response):
    """Test basic CNJ scraping functionality with mocked responses."""
    # Using mock_requests fixture for HTTP
    cnj = scraper('CNJ')
    result = cnj.scrape(pesquisa='teste', paginas=range(0, 1))
    # Verify results
    assert isinstance(result, pl.DataFrame)
    assert len(result) > 0
    for col in ['id', 'texto', 'data']:
        assert col in result.columns
            
def test_cnj_scrape_with_multiple_pages(mock_requests):
    """Test CNJ scraping with multiple pages."""
    cnj = scraper('CNJ')
    dados_cnj = cnj.scrape(pesquisa='golpe do pix', paginas=range(0, 3))
    
    # Should return data from 3 pages (15 items total at 5 per page)
    assert len(dados_cnj) >= 10  # At least 10 results expected
    
    # Verify data structure
    assert 'id' in dados_cnj.columns
    assert 'numeroproccomascara' in dados_cnj.columns
    
def test_cnj_scrape_different_search_term(mock_requests):
    """Test CNJ scraping with different search terms."""
    cnj = scraper('CNJ')
    dados_cnj = cnj.scrape(pesquisa='processo civil', paginas=range(0, 1))
    
    assert dados_cnj is not None
    assert len(dados_cnj) > 0