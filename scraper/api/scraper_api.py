"""
High-level ScraperAPI class that wraps core functionality.

This provides a simple, user-friendly interface for common scraping tasks
without exposing the internal complexity of WebScraper, WebCrawler, etc.
"""

from typing import Optional, Dict, List, Any, Callable
import logging

from ..core import WebScraper, WebCrawler
from ..extractors import BasicExtractor, DataExtractor
from ..utils import save_to_json, save_to_csv
from ..config import get_config, ScraperConfig


class ScraperAPI:
    def __init__(self, delay: float = None, timeout: int = None, config: ScraperConfig = None):
        self.config = config or get_config()
        self.delay = delay if delay is not None else self.config.delay
        self.timeout = timeout if timeout is not None else self.config.timeout
        
        self._scraper = None
        self._crawler = None
        self._extractor = None
        
        self.logger = logging.getLogger(__name__)
    
    def _ensure_initialized(self):
        if self._scraper is None:
            self._scraper = WebScraper(delay=self.delay, timeout=self.timeout)
            self._extractor = BasicExtractor()
            self._crawler = WebCrawler(self._scraper, self._extractor)
    
    def scrape_page(self, url: str) -> Optional[Dict[str, Any]]:
        self._ensure_initialized()
        
        soup = self._scraper.get_page(url)
        if soup is None:
            return None
        
        return {
            'url': url,
            'title': soup.title.string if soup.title else '',
            'text_length': len(soup.get_text(strip=True)),
            'link_count': len(soup.find_all('a')),
            'status': 'success'
        }
    
    def crawl_site(
        self,
        start_url: str,
        max_pages: int = None,
        max_depth: Optional[int] = None,
        stay_within_domain: bool = None,
        url_filter: Optional[Callable[[str], bool]] = None
    ) -> Dict[str, Any]:
        self._ensure_initialized()
        
        max_pages = max_pages if max_pages is not None else self.config.max_pages
        max_depth = max_depth if max_depth is not None else self.config.max_depth
        stay_within_domain = stay_within_domain if stay_within_domain is not None else self.config.stay_within_domain
        
        self.logger.info(f"Starting crawl of {start_url}")
        
        results = self._crawler.crawl(
            start_url=start_url,
            max_pages=max_pages,
            max_depth=max_depth,
            stay_within_domain=stay_within_domain,
            url_filter=url_filter
        )
        
        self.logger.info(f"Crawl complete: {results['stats']['visited_count']} pages visited")
        
        return results
    
    def get_url_statistics(self) -> Dict[str, Any]:
        if self._crawler is None:
            return {'error': 'No crawl performed yet'}
        
        return self._crawler.get_url_statistics()
    
    def get_all_urls(self) -> List[str]:
        if self._crawler is None:
            return []
        
        return self._crawler.get_all_discovered_urls()
    
    def get_visited_urls(self) -> List[str]:
        if self._crawler is None:
            return []
        
        return self._crawler.get_visited_urls()
    
    def save_results(self, filename: str, format: str = 'json') -> bool:
        if self._crawler is None:
            self.logger.error("No crawl results to save")
            return False
        
        try:
            data = self._crawler.get_collected_data()
            if not data:
                self.logger.warning("No data to save")
                return False
            
            if format.lower() == 'json':
                save_to_json(data, filename)
            elif format.lower() == 'csv':
                save_to_csv(data, filename)
            else:
                self.logger.error(f"Unsupported format: {format}")
                return False
            
            self.logger.info(f"Results saved to {filename}.{format}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            return False
    
    def set_custom_extractor(self, extractor: DataExtractor):
        self._extractor = extractor
        if self._crawler is not None:
            self._crawler.extractor = extractor
    
    def close(self):
        if self._scraper is not None:
            self._scraper.close()
            self._scraper = None
            self._crawler = None
            self._extractor = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
