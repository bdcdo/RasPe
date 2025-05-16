# read version from installed package

"""Juscraper: A package for scraping legal data."""

from importlib.metadata import version
from .scraper_manager import scraper

__version__ = version("legiscraper")

__all__ = ["scraper"]
