"""
Batch scraper API for processing multiple sites or large-scale scraping operations.

This provides a high-level interface for batch processing, parallel scraping,
and managing multiple scraping operations.
"""

from typing import List, Dict, Any, Optional, Callable
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core import WebScraper, WebCrawler
from ..extractors import BasicExtractor, RAGExtractor, DataExtractor
from ..utils import save_to_json, save_to_csv
from ..config import get_config, ScraperConfig


class BatchScraper:
    
    def __init__(self, delay: float = None, timeout: int = None, max_workers: int = None, config: ScraperConfig = None):
        self.config = config or get_config()
        self.delay = delay if delay is not None else self.config.delay
        self.timeout = timeout if timeout is not None else self.config.timeout
        self.max_workers = max_workers if max_workers is not None else self.config.max_workers
        
        self.logger = logging.getLogger(__name__)
        self._results = {}
    
    def scrape_multiple_pages(self, urls: List[str]) -> Dict[str, Any]:
        self.logger.info(f"Starting batch scrape of {len(urls)} pages")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self._scrape_single_page, url): url
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results[url] = result
                except Exception as e:
                    self.logger.error(f"Error scraping {url}: {e}")
                    results[url] = {'error': str(e), 'url': url}
        
        self.logger.info(f"Batch scrape complete: {len(results)} pages processed")
        return results
    
    def crawl_multiple_sites(
        self,
        sites: List[Dict[str, Any]],
        extractor_type: str = 'basic'
    ) -> Dict[str, Any]:
        self.logger.info(f"Starting batch crawl of {len(sites)} sites")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_site = {
                executor.submit(self._crawl_single_site, site, extractor_type): site
                for site in sites
            }
            
            for future in as_completed(future_to_site):
                site = future_to_site[future]
                site_url = site['url']
                try:
                    result = future.result()
                    results[site_url] = result
                except Exception as e:
                    self.logger.error(f"Error crawling {site_url}: {e}")
                    results[site_url] = {'error': str(e), 'url': site_url}
        
        self.logger.info(f"Batch crawl complete: {len(results)} sites processed")
        return results
    
    def _scrape_single_page(self, url: str) -> Dict[str, Any]:
        scraper = WebScraper(delay=self.delay, timeout=self.timeout)
        extractor = BasicExtractor()
        crawler = WebCrawler(scraper, extractor)
        
        try:
            soup = scraper.get_page(url)
            if soup is None:
                return {'error': 'Failed to fetch page', 'url': url}
            
            metadata = {'depth': 0, 'url': url}
            data = extractor.extract(url, soup, metadata)
            
            return {
                'url': url,
                'data': data,
                'status': 'success'
            }
            
        finally:
            scraper.close()
    
    def _crawl_single_site(self, site_config: Dict[str, Any], extractor_type: str) -> Dict[str, Any]:
        """Crawl a single site (internal method)."""
        scraper = WebScraper(delay=self.delay, timeout=self.timeout)
        
        if extractor_type.lower() == 'rag':
            extractor = RAGExtractor()
        else:
            extractor = BasicExtractor()
        
        crawler = WebCrawler(scraper, extractor)
        
        try:
            url = site_config['url']
            max_pages = site_config.get('max_pages', 50)
            max_depth = site_config.get('max_depth')
            stay_within_domain = site_config.get('stay_within_domain', True)
            url_filter = site_config.get('url_filter')
            
            results = crawler.crawl(
                start_url=url,
                max_pages=max_pages,
                max_depth=max_depth,
                stay_within_domain=stay_within_domain,
                url_filter=url_filter
            )
            
            return {
                'url': url,
                'results': results,
                'status': 'success'
            }
            
        finally:
            scraper.close()
    
    def get_combined_results(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        total_pages = 0
        total_data = 0
        successful_sites = 0
        failed_sites = 0
        all_data = []
        
        for site_url, result in batch_results.items():
            if 'error' in result:
                failed_sites += 1
                continue
            
            successful_sites += 1
            
            if 'results' in result:
                site_results = result['results']
                total_pages += site_results['stats']['visited_count']
                total_data += site_results['stats']['data_count']
                all_data.extend(site_results['data'])
            elif 'data' in result:
                total_pages += 1
                total_data += 1
                all_data.append(result['data'])
        
        return {
            'summary': {
                'total_sites': len(batch_results),
                'successful_sites': successful_sites,
                'failed_sites': failed_sites,
                'total_pages': total_pages,
                'total_data_entries': total_data
            },
            'all_data': all_data,
            'site_results': batch_results
        }
    
    def save_batch_results(
        self,
        batch_results: Dict[str, Any],
        filename: str,
        format: str = 'json'
    ) -> bool:
        try:
            combined = self.get_combined_results(batch_results)
            
            if format.lower() == 'json':
                save_to_json(combined['all_data'], f"{filename}_combined")
                save_to_json(batch_results, f"{filename}_detailed")
            elif format.lower() == 'csv':
                save_to_csv(combined['all_data'], f"{filename}_combined")
                for site_url, result in batch_results.items():
                    safe_filename = site_url.replace('://', '_').replace('/', '_').replace(':', '_')
                    if 'results' in result and 'data' in result['results']:
                        save_to_csv(result['results']['data'], f"{filename}_{safe_filename}")
            else:
                self.logger.error(f"Unsupported format: {format}")
                return False
            
            self.logger.info(f"Batch results saved with prefix: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save batch results: {e}")
            return False
    
    def create_site_configs(
        self,
        urls: List[str],
        max_pages: int = 50,
        max_depth: Optional[int] = None,
        stay_within_domain: bool = True
    ) -> List[Dict[str, Any]]:
        return [
            {
                'url': url,
                'max_pages': max_pages,
                'max_depth': max_depth,
                'stay_within_domain': stay_within_domain
            }
            for url in urls
        ]
    
    def add_url_filter(self, site_configs: List[Dict[str, Any]], filter_func: Callable[[str], bool]):
        for config in site_configs:
            config['url_filter'] = filter_func
