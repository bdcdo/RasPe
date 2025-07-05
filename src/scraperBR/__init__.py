from importlib.metadata import version
from .scraper_manager import scraper
from .utils import expand, remove_duplicates, extract, check

__version__ = version("scraperBR")

__all__ = ["scraper", "expand", "remove_duplicates", "extract", "check"]
