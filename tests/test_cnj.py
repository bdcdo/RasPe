import pytest
import legiscraper as legis


class TestCNJScraper:
    """Test suite for CNJ scraper functionality."""
    
    def test_cnj_scraper_creation(self):
        """Test that CNJ scraper can be created successfully."""
        cnj = legis.scraper('CNJ')
        assert cnj is not None
        
    def test_cnj_scrape_basic(self):
        """Test basic CNJ scraping functionality with small dataset."""
        cnj = legis.scraper('CNJ')
        dados_cnj = cnj.scrape(pesquisa='golpe do pix', paginas=range(0, 2))
        
        # Verify we got data back
        assert dados_cnj is not None
        assert len(dados_cnj) > 0
        
        # Verify expected columns exist
        expected_columns = ['id', 'data_disponibilizacao', 'siglaTribunal', 'tipoComunicacao']
        for col in expected_columns:
            assert col in dados_cnj.columns
            
    def test_cnj_scrape_with_multiple_pages(self):
        """Test CNJ scraping with multiple pages."""
        cnj = legis.scraper('CNJ')
        dados_cnj = cnj.scrape(pesquisa='golpe do pix', paginas=range(0, 3))
        
        # Should return data from 3 pages (15 items total at 5 per page)
        assert len(dados_cnj) >= 10  # At least 10 results expected
        
        # Verify data structure
        assert 'id' in dados_cnj.columns
        assert 'numeroproccomascara' in dados_cnj.columns
        
    def test_cnj_scrape_different_search_term(self):
        """Test CNJ scraping with different search terms."""
        cnj = legis.scraper('CNJ')
        dados_cnj = cnj.scrape(pesquisa='processo civil', paginas=range(0, 1))
        
        assert dados_cnj is not None
        assert len(dados_cnj) > 0