from typing import Dict, Any
from bs4 import BeautifulSoup

from .base import DataExtractor


class BasicExtractor(DataExtractor):
    
    def extract(self, url: str, soup: BeautifulSoup, metadata: Dict[str, Any]) -> Dict:
        return {
            'url': url,
            'depth': metadata.get('depth', 0),
            'title': soup.title.string if soup.title else '',
            'text_length': len(soup.get_text(strip=True)),
            'link_count': len(soup.find_all('a'))
        }
