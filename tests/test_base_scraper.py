"""Tests for the base scraper functionality."""
from pathlib import Path
from unittest.mock import MagicMock, patch # Retain, might be useful for new tests

import polars as pl
import pytest
import requests # Retain, might be useful for new tests

from src.legiscraper.base_scraper import BaseScraper, HTMLScraper # Add HTMLScraper
from src.legiscraper.scrapers.presidencia import ScraperPresidencia
# from src.legiscraper.scrapers.comunica_cnj import ComunicaCNJScraper # TODO: Uncomment and ensure this scraper is available

# TODO: Expand test coverage significantly. Many BaseScraper methods are untested.
# TODO: Per project guidelines (MEMORY[tests.md]), tests should be parameterized or duplicated
#       to run with instances of both ScraperPresidencia and ComunicaCNJScraper
#       to ensure abstract method implementations are also covered.

class TestBaseScraper:
    """Test suite for BaseScraper class."""

    @pytest.fixture
    def presidencia_scraper(self, tmp_path: Path) -> ScraperPresidencia:
        """Fixture for ScraperPresidencia instance."""
        return ScraperPresidencia(download_path=str(tmp_path / "presidencia_data"))

    # TODO: Add a similar fixture for ComunicaCNJScraper when available and integrated.
    # @pytest.fixture
    # def cnj_scraper(self, tmp_path: Path) -> ComunicaCNJScraper:
    #     """Fixture for ComunicaCNJScraper instance."""
    #     return ComunicaCNJScraper(download_path=str(tmp_path / "cnj_data"))

    def test_initialization(self, presidencia_scraper: ScraperPresidencia):
        """Test that the scraper initializes with default values."""
        # TODO: Consider parameterizing to test with debug=False.
        # Arrange & Act
        scraper = presidencia_scraper # Use fixture

        # Assert
        assert scraper.nome_buscador == "PRESIDENCIA"
        assert "legislacao.presidencia.gov.br" in scraper.api_base
        assert scraper.session is not None
        assert scraper.logger is not None
        assert scraper.debug is True # Default is True

    def test_base_scraper_is_abstract(self):
        """Test that BaseScraper cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseScraper("foo_abstract_scraper") # type: ignore

    def test_set_download_path(self, presidencia_scraper: ScraperPresidencia, tmp_path: Path):
        """Test setting a custom download path during scraper initialization."""
        # Arrange
        # ScraperPresidencia is instantiated by the fixture with a download_path

        # Assert download directory creation (done by fixture)
        # The presidencia_scraper fixture creates a ScraperPresidencia instance
        # with download_path=str(tmp_path / "presidencia_data").
        # The _set_download_path method (called in BaseScraper's __init__ if path is provided)
        # should create this directory.
        assert (tmp_path / "presidencia_data").exists()
        assert presidencia_scraper.download_path == str(tmp_path / "presidencia_data")

    # TODO: Test `_set_download_path` specifically for the case where `download_path` is None
    #       in the scraper's __init__, and a temporary directory should be created by `_create_download_dir`.
    #       This would likely involve instantiating a scraper with download_path=None and then checking
    #       if scraper.download_path is set and the directory exists.
    # def test_set_download_path_creates_temp_dir_if_none(self, tmp_path: Path):
    #     scraper = ScraperPresidencia(download_path=None) # Temporarily override fixture or create new instance
    #     # _create_download_dir is called by _set_download_path if path is None and dir doesn't exist
    #     # or directly by methods like scrape/download_data if download_path is still None.
    #     # For this test, we assume __init__ -> _set_download_path -> _create_download_dir sequence.
    #     assert scraper.download_path is not None
    #     assert Path(scraper.download_path).exists()
    #     assert Path(scraper.download_path).is_dir()
    #     # Ensure it's a temporary directory (e.g., in tempfile.gettempdir() or similar)
    #     # This might be tricky to assert precisely without more control or knowledge of temp dir naming.


    # --- Placeholder comments for new test methods ---

    # TODO: Test `_create_download_dir` specifically for the case where `download_path` is None
    #       and a temporary directory should be created.
    # def test_create_temp_download_dir(self):
    #     scraper = ScraperPresidencia(download_path=None) # Or a generic mock scraper
    #     scraper._create_download_dir()
    #     assert scraper.download_path is not None
    #     assert Path(scraper.download_path).exists()
    #     # Remember to clean up if not using pytest's tmp_path features directly for this

    # TODO: Add comprehensive tests for the `scrape` method.
    # This is a critical public method. Tests should cover:
    # - Mocking network requests (e.g., self.session.request, _set_r).
    # - Mocking abstract method implementations from a concrete scraper.
    # - Scenarios: single/multiple pages, no results, list/tuple kwargs for iterative scraping.
    # - Error handling (network, parsing).
    # - Assertion of the final combined DataFrame.
    # - Consider a test using a small, controlled set of *real (but static/local) data*
    #   for an end-to-end check of core logic, complementing mock-heavy tests.
    #   This helps verify the integration of various helper methods.
    # def test_scrape_functionality(self, presidencia_scraper, mocker): # Add cnj_scraper_fixture later
    #     pass

    # TODO: Add tests for the `download_data` method.
    # This is another critical public method. Tests should cover:
    # - Mocking network interactions and abstract methods.
    # - Verification of downloaded files (mocked content and file paths).
    # - Pagination logic (`_set_paginas`, `_set_query_atual`).
    # - File naming (`_set_file_name`).
    # - Behavior with debug=True (files kept) vs. debug=False (temp files cleaned up if applicable).
    # - A test with *real (but static/local) data* for a specific, simple download scenario
    #   could be valuable to ensure the request formation and basic file handling work as expected.
    # def test_download_data_functionality(self, presidencia_scraper, mocker): # Add cnj_scraper_fixture later
    #     pass

    # TODO: Add tests for `_remove_duplicates` method.
    # Key data processing step. Tests should cover:
    # - DataFrame with no duplicates.
    # - DataFrame with duplicates, checking if `termo_busca` is correctly aggregated.
    # - DataFrame with duplicates and usage of `exclude_cols_from_dedup`.
    # - DataFrame without 'termo_busca' column.
    # - Empty DataFrame.
    # - Use *real-world-like example data* (even if mocked) that represents typical duplicate scenarios.
    # def test_remove_duplicates(self, presidencia_scraper): # Add cnj_scraper_fixture later
    #     # Example:
    #     # scraper = presidencia_scraper
    #     # data = {
    #     #     "id": [1, 2, 1, 3],
    #     #     "value": ["a", "b", "a", "c"],
    #     #     "termo_busca": ["query1", "query2", "query3", "query1"]
    #     # }
    #     # df = pl.DataFrame(data)
    #     # result_df = scraper._remove_duplicates(df)
    #     # Assert expected shape and content, especially aggregated 'termo_busca'.
    #     pass

    # TODO: Add tests for `parse_data` method.
    # Handles parsing of downloaded files. Tests should cover:
    # - Parsing a single file.
    # - Parsing a directory with multiple files (mock `_parse_page` for each).
    # - Parsing a directory with a mix of valid and invalid/corrupt files (testing error handling).
    # - Parsing an empty directory or non-existent path.
    # - Mocking `_parse_page` to return specific DataFrames or raise errors.
    # - Verifying schema consistency checks and warnings.
    # - Testing with *sample real data files* (e.g., a small JSON or HTML snippet,
    #   placed in tmp_path) to ensure `_parse_page` (when implemented by a subclass)
    #   integrates correctly with `parse_data`.
    # def test_parse_data(self, presidencia_scraper, mocker, tmp_path): # Add cnj_scraper_fixture later
    #     pass

    # TODO: Ensure internal helper methods (_config, _get_n_pags, _set_paginas,
    # _set_file_name, _set_query_atual, _set_r) are adequately covered
    # through tests of `scrape` and `download_data`.
    # Direct tests for `_set_r` (mocking `requests.Session.request`) are highly recommended
    # to cover retry logic, different HTTP methods (GET/POST), and error handling.
    # def test_set_r_functionality(self, presidencia_scraper, mocker):
    #     # Mock scraper.session.request
    #     pass

class TestHTMLScraper:
    """Test suite for HTMLScraper mixin class."""

    class DummyHTMLScraper(HTMLScraper): # Concrete class for testing mixin
        pass

    @pytest.fixture
    def html_scraper(self) -> DummyHTMLScraper:
        return self.DummyHTMLScraper()

    # TODO: Add tests for `HTMLScraper.soup_it`.
    # This utility is for HTML parsing. Tests should cover:
    # - Valid HTML string.
    # - Valid HTML bytes.
    # - Empty string/bytes.
    # - Malformed HTML (how `BeautifulSoup` handles it, e.g., does not raise error but returns a soup object).
    # - Using a *small, representative HTML snippet* as input would be good.
    def test_soup_it_with_string(self, html_scraper: DummyHTMLScraper):
        from bs4 import BeautifulSoup # Ensure bs4 is a test dependency or handle import
        html_content = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        soup = html_scraper.soup_it(html_content)
        assert isinstance(soup, BeautifulSoup)
        assert soup.find("h1").text == "Test"
        assert soup.find("p").text == "Content"

    def test_soup_it_with_bytes(self, html_scraper: DummyHTMLScraper):
        from bs4 import BeautifulSoup
        html_content_bytes = b"<html><body><h1>Bytes Test</h1></body></html>"
        soup = html_scraper.soup_it(html_content_bytes)
        assert isinstance(soup, BeautifulSoup)
        assert soup.find("h1").text == "Bytes Test"

    def test_soup_it_empty_input(self, html_scraper: DummyHTMLScraper):
        from bs4 import BeautifulSoup
        soup_empty_str = html_scraper.soup_it("")
        assert isinstance(soup_empty_str, BeautifulSoup)
        # Behavior of BeautifulSoup with empty string might vary or be minimal.
        # Check for a non-None result and perhaps that it has no child elements.
        assert len(list(soup_empty_str.children)) == 0 

        soup_empty_bytes = html_scraper.soup_it(b"")
        assert isinstance(soup_empty_bytes, BeautifulSoup)
        # BeautifulSoup treats b"" as a NavigableString, which counts as one child.
        assert len(list(soup_empty_bytes.children)) == 1
        child_node = list(soup_empty_bytes.children)[0]
        from bs4.element import NavigableString # Import for precise type check
        assert isinstance(child_node, NavigableString)
        assert child_node.get_text() == "b''"  # Check decoded textual content
        assert child_node.string == "b''"      # Check raw string content of the NavigableString for b'' input
