"""Configuration file for pytest."""
import sys, os
# adicionar raiz do projeto para resolver pacote src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
import requests
import polars as pl

from src.legiscraper.scrapers.comunicaCNJ import comunicaCNJ_Scraper
from src.legiscraper.scrapers.presidencia import ScraperPresidencia
from src.legiscraper.base_scraper import BaseScraper

@pytest.fixture(scope="function")
def mock_response() -> Generator[MagicMock, None, None]:
    """Fixture to mock HTTP responses."""
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    mock_response.text = ""
    mock_response.content = b""
    mock_response.json.return_value = {
        "total": 1,
        "itens": [{"id": 1, "texto": "Teste"}]
    }
    
    yield mock_response

@pytest.fixture
def mock_requests(mock_response: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock requests.get/post to return our mock response."""
    def mock_get(*args, **kwargs):
        return mock_response
    
    def mock_post(*args, **kwargs):
        return mock_response
    
    monkeypatch.setattr(requests.Session, "get", mock_get)
    monkeypatch.setattr(requests.Session, "post", mock_post)
    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(requests, "post", mock_post)

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create and clean up a temporary directory for tests."""
    import tempfile
    import shutil
    
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def base_scraper() -> BaseScraper:
    """Create a base scraper instance for testing."""
    return BaseScraper("test_scraper")

@pytest.fixture
def cnj_scraper() -> comunicaCNJ_Scraper:
    """Create a CNJ scraper instance for testing."""
    return comunicaCNJ_Scraper()

@pytest.fixture
def presidencia_scraper() -> ScraperPresidencia:
    """Create a Presidência scraper instance for testing."""
    return ScraperPresidencia()

@pytest.fixture
def sample_dataframe() -> pl.DataFrame:
    """Create a sample DataFrame for testing."""
    return pl.DataFrame({
        "id": [1, 2, 3],
        "texto": ["teste 1", "teste 2", "teste 3"],
        "data": ["2023-01-01", "2023-01-02", "2023-01-03"]
    })
