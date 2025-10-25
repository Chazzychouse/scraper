from typing import Dict, List, Any
from bs4 import BeautifulSoup

from .base import DataExtractor


class RAGExtractor(DataExtractor):
    
    def __init__(self, chunk_size_target: int = 500):
        self.chunk_size_target = chunk_size_target
    
    def extract(self, url: str, soup: BeautifulSoup, metadata: Dict[str, Any]) -> List[Dict]:
        chunks = []
        
        page_title = soup.title.string if soup.title else ''
        
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find(class_='content') or
            soup.find(id='content') or
            soup
        )
        
        current_section = {'h1': '', 'h2': '', 'h3': '', 'content': []}
        
        h1 = main_content.find('h1')
        if h1:
            current_section['h1'] = h1.get_text(strip=True)
        
        for element in main_content.find_all(['h2', 'h3', 'p', 'ul', 'ol', 'pre']):
            if element.name == 'h2':
                if current_section['content']:
                    chunks.append(self._create_chunk(current_section, url, page_title, metadata))
                current_section = {
                    'h1': current_section['h1'],
                    'h2': element.get_text(strip=True),
                    'h3': '',
                    'content': []
                }
            elif element.name == 'h3':
                if len(' '.join(current_section['content'])) > self.chunk_size_target * 1.5:
                    chunks.append(self._create_chunk(current_section, url, page_title, metadata))
                    current_section['content'] = []
                current_section['h3'] = element.get_text(strip=True)
            else:
                text = element.get_text(strip=True)
                if text:
                    if element.name == 'pre':
                        text = f"[CODE]\n{text}\n[/CODE]"
                    current_section['content'].append(text)
        
        if current_section['content']:
            chunks.append(self._create_chunk(current_section, url, page_title, metadata))
        
        return chunks
    
    def _create_chunk(self, section: Dict, url: str, page_title: str, metadata: Dict) -> Dict:
        """Create a RAG-optimized chunk."""
        content_text = ' '.join(section['content'])
        title_parts = [p for p in [section['h1'], section['h2'], section['h3']] if p]
        full_title = ' > '.join(title_parts) if title_parts else page_title
        
        return {
            'text': content_text,
            'title': full_title,
            'page_title': page_title,
            'h1': section['h1'],
            'h2': section['h2'],
            'h3': section['h3'],
            'url': url,
            'source': url,
            'depth': metadata.get('depth', 0),
            'char_count': len(content_text),
            'chunk_id': f"{url}#{'-'.join(title_parts)}"
        }
