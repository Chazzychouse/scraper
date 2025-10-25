from typing import Optional, Dict, List, Any, Set, Callable
import logging
from collections import deque

from .scraper import WebScraper
from ..extractors.base import DataExtractor
from ..utils.url_filter import URLFilter


class WebCrawler:
    
    def __init__(self, scraper: WebScraper, extractor: Optional[DataExtractor] = None):
        self.scraper = scraper
        self.extractor = extractor
        
        # Crawl state
        self.visited_urls: Set[str] = set()
        self.to_visit: deque = deque()
        self.collected_urls: List[str] = []
        self.collected_data: List[Any] = []
        
        self.logger = logging.getLogger(__name__)
    
    def crawl(
        self,
        start_url: str,
        max_depth: Optional[int] = None,
        max_pages: Optional[int] = None,
        stay_within_domain: bool = True,
        url_filter: Optional[Callable[[str], bool]] = None
    ) -> Dict[str, Any]:
        self._reset()
        
        start_url = URLFilter.normalize_url(start_url)
        if not URLFilter.is_valid_url(start_url):
            raise ValueError(f"Invalid start URL: {start_url}")
        
        base_domain = URLFilter.get_domain(start_url)
        
        self.to_visit.append((start_url, 0))
        
        self.logger.info(f"Starting crawl from: {start_url}")
        self.logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}")
        
        while self.to_visit:
            if max_pages and len(self.visited_urls) >= max_pages:
                self.logger.info(f"Reached max_pages limit: {max_pages}")
                break
            
            current_url, depth = self.to_visit.popleft()
            
            if max_depth is not None and depth > max_depth:
                continue
            
            if current_url in self.visited_urls:
                continue
            
            if url_filter and not url_filter(current_url):
                continue
            
            self.visited_urls.add(current_url)
            self.collected_urls.append(current_url)
            
            self.logger.info(
                f"Visiting [{depth}]: {current_url} "
                f"({len(self.visited_urls)}/{max_pages or '∞'})"
            )
            
            soup = self.scraper.get_page(current_url)
            if soup is None:
                continue
            
            if self.extractor:
                try:
                    metadata = {'depth': depth, 'url': current_url}
                    extracted = self.extractor.extract(current_url, soup, metadata)
                    
                    if extracted is not None:
                        if isinstance(extracted, list):
                            self.collected_data.extend(extracted)
                        else:
                            self.collected_data.append(extracted)
                            
                except Exception as e:
                    self.extractor.on_extraction_error(current_url, e)
            
            links = self.scraper.extract_links(soup, current_url)
            for link in links:
                normalized_link = URLFilter.normalize_url(link)
                
                if self._should_visit(
                    normalized_link,
                    base_domain,
                    stay_within_domain,
                    url_filter
                ):
                    self.to_visit.append((normalized_link, depth + 1))
        
        self.logger.info(f"Crawl complete. Visited {len(self.visited_urls)} pages.")
        
        return self.get_results()
    
    def _should_visit(
        self,
        url: str,
        base_domain: str,
        stay_within_domain: bool,
        url_filter: Optional[Callable]
    ) -> bool:
        if url in self.visited_urls:
            return False
        
        if not URLFilter.is_valid_url(url):
            return False
        
        if stay_within_domain and not URLFilter.same_domain(url, base_domain):
            return False
        
        if url_filter and not url_filter(url):
            return False
        
        return True
    
    def get_results(self) -> Dict[str, Any]:
        return {
            'urls': self.collected_urls,
            'data': self.collected_data,
            'stats': {
                'visited_count': len(self.visited_urls),
                'queued_count': len(self.to_visit),
                'collected_count': len(self.collected_urls),
                'data_count': len(self.collected_data)
            }
        }
    
    def get_total_urls(self) -> int:
        return len(self.visited_urls) + len(self.to_visit)
    
    def get_visited_urls(self) -> List[str]:
        return list(self.visited_urls)
    
    def get_queued_urls(self) -> List[str]:
        return [url for url, depth in self.to_visit]
    
    def get_all_discovered_urls(self) -> List[str]:
        return list(self.visited_urls) + [url for url, depth in self.to_visit]
    
    def get_url_statistics(self) -> Dict[str, Any]:
        visited_count = len(self.visited_urls)
        queued_count = len(self.to_visit)
        total_count = visited_count + queued_count
        
        return {
            'total_urls': total_count,
            'visited_urls': visited_count,
            'queued_urls': queued_count,
            'visited_percentage': (visited_count / total_count * 100) if total_count > 0 else 0,
            'queued_percentage': (queued_count / total_count * 100) if total_count > 0 else 0
        }
    
    def get_domain_urls(self, domain: str) -> List[str]:
        all_urls = self.get_all_discovered_urls()
        return [url for url in all_urls if domain in url]
    
    def get_urls_by_depth(self, target_depth: int) -> List[str]:
        return [url for url, depth in self.to_visit if depth == target_depth]
    
    def _reset(self):
        self.visited_urls.clear()
        self.to_visit.clear()
        self.collected_urls.clear()
        self.collected_data.clear()
