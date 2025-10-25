from abc import ABC, abstractmethod
from typing import Dict, Any
from bs4 import BeautifulSoup
import logging


class DataExtractor(ABC):
    
    @abstractmethod
    def extract(self, url: str, soup: BeautifulSoup, metadata: Dict[str, Any]) -> Any:
        pass
    
    def on_extraction_error(self, url: str, error: Exception):
        logging.error(f"Extraction error on {url}: {error}")
