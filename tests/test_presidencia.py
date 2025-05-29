import pytest
import legiscraper as legis


class TestPresidenciaScraper:
    """Test suite for Presidencia scraper functionality."""
    
    def test_presidencia_scraper_creation(self):
        """Test that Presidencia scraper can be created successfully."""
        scraper_presidencia = legis.scraper('PRESIDENCIA')
        assert scraper_presidencia is not None
        
    def test_presidencia_scrape_basic(self):
        """Test basic Presidencia scraping functionality with small dataset."""
        scraper_presidencia = legis.scraper('PRESIDENCIA')
        dados = scraper_presidencia.scrape(pesquisa='doença raras', paginas=range(0, 2))
        
        # Verify we got data back
        assert dados is not None
        assert len(dados) > 0
        
        # Verify expected columns exist based on notebook output
        expected_columns = ['nome', 'link', 'ficha', 'revogacao', 'descricao']
        for col in expected_columns:
            assert col in dados.columns
            
    def test_presidencia_scrape_with_multiple_pages(self):
        """Test Presidencia scraping with multiple pages."""
        scraper_presidencia = legis.scraper('PRESIDENCIA')
        dados = scraper_presidencia.scrape(pesquisa='doença raras', paginas=range(0, 3))
        
        # Should return data from 3 pages (30 items total based on notebook)
        assert len(dados) >= 20  # At least 20 results expected
        
        # Verify data structure
        assert 'nome' in dados.columns
        assert 'link' in dados.columns
        assert 'descricao' in dados.columns
        
    def test_presidencia_scrape_different_search_term(self):
        """Test Presidencia scraping with different search terms."""
        scraper_presidencia = legis.scraper('PRESIDENCIA')
        dados = scraper_presidencia.scrape(pesquisa='saude publica', paginas=range(0, 1))
        
        assert dados is not None
        assert len(dados) > 0
        
    def test_presidencia_data_structure(self):
        """Test that returned data has correct structure and types."""
        scraper_presidencia = legis.scraper('PRESIDENCIA')
        dados = scraper_presidencia.scrape(pesquisa='doença raras', paginas=range(0, 1))
        
        # Check that we have the expected columns with non-empty data
        assert 'nome' in dados.columns
        assert 'link' in dados.columns
        assert 'ficha' in dados.columns
        assert 'revogacao' in dados.columns
        assert 'descricao' in dados.columns
        
        # Verify that links are properly formatted URLs
        first_row = dados.row(0, named=True)
        assert first_row['link'].startswith('https://')
        assert first_row['ficha'].startswith('https://')
        
        # Verify nome is not empty
        assert len(first_row['nome'].strip()) > 0