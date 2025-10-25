import requests
from bs4 import BeautifulSoup
from typing import Optional, List
import time
import logging
from urllib.parse import urljoin

from ..config import get_config, ScraperConfig


class WebScraper:
    
    def __init__(self, delay: float = None, timeout: int = None, config: ScraperConfig = None):
        self.config = config or get_config()
        
        self.delay = delay if delay is not None else self.config.delay
        self.timeout = timeout if timeout is not None else self.config.timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent
        })
        
        logging.basicConfig(level=getattr(logging, self.config.log_level))
        self.logger = logging.getLogger(__name__)
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            self.logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            time.sleep(self.delay)
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, soup: BeautifulSoup, base_url: str = None) -> List[str]:
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if base_url:
                href = urljoin(base_url, href)
            links.append(href)
        return links
    
    def extract_text(self, soup: BeautifulSoup, selector: str = None) -> str:
        if selector:
            elements = soup.select(selector)
            return ' '.join([elem.get_text(strip=True) for elem in elements])
        else:
            return soup.get_text(strip=True)
    
    def close(self):
        self.session.close()
