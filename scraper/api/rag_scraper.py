"""
RAG-optimized scraper API for Retrieval-Augmented Generation systems.

This provides a specialized interface for extracting content optimized for RAG systems.
"""

from typing import Optional, Dict, List, Any, Callable
import logging

from ..core import WebScraper, WebCrawler
from ..extractors import RAGExtractor
from ..utils import save_to_json, save_to_csv
from ..config import get_config, ScraperConfig


class RAGScraper:
    
    def __init__(self, chunk_size: int = None, delay: float = None, timeout: int = None, config: ScraperConfig = None):
        self.config = config or get_config()
        self.chunk_size = chunk_size if chunk_size is not None else self.config.chunk_size
        self.delay = delay if delay is not None else self.config.delay
        self.timeout = timeout if timeout is not None else self.config.timeout
        
        self._scraper = None
        self._crawler = None
        self._extractor = None
        
        self.logger = logging.getLogger(__name__)
    
    def _ensure_initialized(self):
        """Ensure the scraper is initialized."""
        if self._scraper is None:
            self._scraper = WebScraper(delay=self.delay, timeout=self.timeout)
            self._extractor = RAGExtractor(chunk_size_target=self.chunk_size)
            self._crawler = WebCrawler(self._scraper, self._extractor)
    
    def extract_from_page(self, url: str) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        
        soup = self._scraper.get_page(url)
        if soup is None:
            return []
        
        metadata = {'depth': 0, 'url': url}
        chunks = self._extractor.extract(url, soup, metadata)
        
        return chunks if chunks else []
    
    def crawl_for_rag(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: Optional[int] = None,
        stay_within_domain: bool = True,
        url_filter: Optional[Callable[[str], bool]] = None
    ) -> Dict[str, Any]:
        self._ensure_initialized()
        
        self.logger.info(f"Starting RAG crawl of {start_url}")
        
        results = self._crawler.crawl(
            start_url=start_url,
            max_pages=max_pages,
            max_depth=max_depth,
            stay_within_domain=stay_within_domain,
            url_filter=url_filter
        )
        
        chunks = results['data']
        if chunks:
            chunk_sizes = [chunk.get('char_count', 0) for chunk in chunks]
            results['rag_stats'] = {
                'total_chunks': len(chunks),
                'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
                'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
                'chunks_per_page': len(chunks) / results['stats']['visited_count'] if results['stats']['visited_count'] > 0 else 0
            }
        
        self.logger.info(f"RAG crawl complete: {len(chunks)} chunks from {results['stats']['visited_count']} pages")
        
        return results
    
    def get_chunks(self) -> List[Dict[str, Any]]:
        if self._crawler is None:
            return []
        
        return self._crawler.get_collected_data()
    
    def get_chunks_by_page(self, url: str) -> List[Dict[str, Any]]:
        all_chunks = self.get_chunks()
        return [chunk for chunk in all_chunks if chunk.get('url') == url]
    
    def get_chunks_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        all_chunks = self.get_chunks()
        topic_lower = topic.lower()
        
        return [
            chunk for chunk in all_chunks
            if topic_lower in chunk.get('text', '').lower() or
               topic_lower in chunk.get('title', '').lower()
        ]
    
    def get_chunk_statistics(self) -> Dict[str, Any]:
        chunks = self.get_chunks()
        if not chunks:
            return {'error': 'No chunks available'}
        
        chunk_sizes = [chunk.get('char_count', 0) for chunk in chunks]
        titles = [chunk.get('title', '') for chunk in chunks]
        
        unique_pages = len(set(chunk.get('url', '') for chunk in chunks))
        
        h1_count = len([chunk for chunk in chunks if chunk.get('h1')])
        h2_count = len([chunk for chunk in chunks if chunk.get('h2')])
        h3_count = len([chunk for chunk in chunks if chunk.get('h3')])
        
        return {
            'total_chunks': len(chunks),
            'unique_pages': unique_pages,
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'chunks_with_h1': h1_count,
            'chunks_with_h2': h2_count,
            'chunks_with_h3': h3_count,
            'avg_title_length': sum(len(title) for title in titles) / len(titles) if titles else 0
        }
    
    def save_chunks(self, filename: str, format: str = 'json') -> bool:
        chunks = self.get_chunks()
        if not chunks:
            self.logger.error("No chunks to save")
            return False
        
        try:
            if format.lower() == 'json':
                save_to_json(chunks, filename)
            elif format.lower() == 'csv':
                save_to_csv(chunks, filename)
            else:
                self.logger.error(f"Unsupported format: {format}")
                return False
            
            self.logger.info(f"Chunks saved to {filename}.{format}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save chunks: {e}")
            return False
    
    def export_for_rag_framework(self, framework: str = 'langchain') -> List[Dict[str, Any]]:
        chunks = self.get_chunks()
        
        if framework.lower() == 'langchain':
            return [
                {
                    'page_content': chunk.get('text', ''),
                    'metadata': {
                        'source': chunk.get('url', ''),
                        'title': chunk.get('title', ''),
                        'h1': chunk.get('h1', ''),
                        'h2': chunk.get('h2', ''),
                        'h3': chunk.get('h3', ''),
                        'chunk_id': chunk.get('chunk_id', ''),
                        'char_count': chunk.get('char_count', 0)
                    }
                }
                for chunk in chunks
            ]
        
        elif framework.lower() == 'llamaindex':
            return [
                {
                    'text': chunk.get('text', ''),
                    'metadata': {
                        'url': chunk.get('url', ''),
                        'title': chunk.get('title', ''),
                        'headings': [h for h in [chunk.get('h1'), chunk.get('h2'), chunk.get('h3')] if h],
                        'chunk_id': chunk.get('chunk_id', '')
                    }
                }
                for chunk in chunks
            ]
        
        else:
            return chunks
    
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
