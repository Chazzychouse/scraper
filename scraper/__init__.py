__version__ = "0.0.1"
__author__ = "Chazzychouse"

from .core.scraper import WebScraper
from .core.crawler import WebCrawler

from .extractors.base import DataExtractor
from .extractors.basic import BasicExtractor
from .extractors.rag import RAGExtractor

from .api.scraper_api import ScraperAPI
from .api.rag_scraper import RAGScraper
from .api.batch_scraper import BatchScraper

from .utils.data_save import save_to_json, save_to_csv
from .utils.url_filter import URLFilter

__all__ = [
    'WebScraper',
    'WebCrawler',
    
    'DataExtractor',
    'BasicExtractor', 
    'RAGExtractor',
    
    'ScraperAPI',
    'RAGScraper',
    'BatchScraper',
    
    'save_to_json',
    'save_to_csv',
    'URLFilter',
]