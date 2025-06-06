# read version from installed package

"""Juscraper: A package for scraping legal data."""

from importlib.metadata import version
from .scraper_manager import scraper
from .utils import expand

__version__ = version("buscraper")

__all__ = ["scraper", "expand"]
