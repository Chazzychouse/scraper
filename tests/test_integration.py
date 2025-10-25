import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
from scraper.api.scraper_api import ScraperAPI
from scraper.api.batch_scraper import BatchScraper
from scraper.api.rag_scraper import RAGScraper
from scraper.core.scraper import WebScraper
from scraper.core.crawler import WebCrawler
from scraper.extractors.basic import BasicExtractor
from scraper.extractors.rag import RAGExtractor


class TestScraperAPIIntegration:
    
    @pytest.fixture
    def mock_web_scraper(self):
        scraper = Mock(spec=WebScraper)
        return scraper
    
    @pytest.fixture
    def sample_html_pages(self):
        return {
            'home': """
            <html>
                <head><title>Home Page</title></head>
                <body>
                    <h1>Welcome to Example Site</h1>
                    <p>This is the home page content.</p>
                    <a href="/about">About Us</a>
                    <a href="/products">Products</a>
                    <a href="/contact">Contact</a>
                </body>
            </html>
            """,
            'about': """
            <html>
                <head><title>About Us</title></head>
                <body>
                    <h1>About Our Company</h1>
                    <p>We are a leading company in our industry.</p>
                    <a href="/">Home</a>
                    <a href="/team">Our Team</a>
                </body>
            </html>
            """,
            'products': """
            <html>
                <head><title>Our Products</title></head>
                <body>
                    <h1>Product Catalog</h1>
                    <p>Check out our amazing products.</p>
                    <a href="/">Home</a>
                    <a href="/product/1">Product 1</a>
                    <a href="/product/2">Product 2</a>
                </body>
            </html>
            """
        }
    
    def test_full_crawl_workflow(self, mock_web_scraper, sample_html_pages):
        def mock_get_page(url):
            if 'about' in url:
                return BeautifulSoup(sample_html_pages['about'], 'html.parser')
            elif 'products' in url:
                return BeautifulSoup(sample_html_pages['products'], 'html.parser')
            else:
                return BeautifulSoup(sample_html_pages['home'], 'html.parser')
        
        def mock_extract_links(soup, base_url=None):
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/'):
                    links.append(f"https://example.com{href}")
                elif href.startswith('http'):
                    links.append(href)
            return links
        
        mock_web_scraper.get_page.side_effect = mock_get_page
        mock_web_scraper.extract_links.side_effect = mock_extract_links
        
        with patch('scraper.api.scraper_api.WebScraper', return_value=mock_web_scraper):
            api = ScraperAPI(delay=0, timeout=10)
            
            results = api.crawl_site('https://example.com', max_pages=3, max_depth=2)
            
            assert results['stats']['visited_count'] >= 1
            assert len(results['urls']) >= 1
            assert len(results['data']) >= 1
            
            for data_item in results['data']:
                assert 'url' in data_item
                assert 'title' in data_item
                assert 'text_length' in data_item
                assert 'link_count' in data_item
                assert 'depth' in data_item
            
            url_stats = api.get_url_statistics()
            assert 'total_urls' in url_stats
            assert url_stats['total_urls'] >= 1
            
            all_urls = api.get_all_urls()
            assert len(all_urls) >= 1
            
            visited_urls = api.get_visited_urls()
            assert len(visited_urls) >= 1
    
    def test_save_results_workflow(self, mock_web_scraper, sample_html_pages, tmp_path):
        soup = BeautifulSoup(sample_html_pages['home'], 'html.parser')
        mock_web_scraper.get_page.return_value = soup
        mock_web_scraper.extract_links.return_value = ['https://example.com/about']
        
        with patch('scraper.api.scraper_api.WebScraper', return_value=mock_web_scraper), \
             patch('scraper.api.scraper_api.save_to_json') as mock_save_json, \
             patch('scraper.api.scraper_api.save_to_csv') as mock_save_csv:
            
            api = ScraperAPI(delay=0, timeout=10)
            
            results = api.crawl_site('https://example.com', max_pages=2)
            
            json_success = api.save_results('test_results', 'json')
            assert json_success is True
            mock_save_json.assert_called_once()
            
            csv_success = api.save_results('test_results', 'csv')
            assert csv_success is True
            mock_save_csv.assert_called_once()
    
    def test_custom_extractor_workflow(self, mock_web_scraper, sample_html_pages):
        class CustomExtractor(BasicExtractor):
            def extract(self, url, soup, metadata):
                base_data = super().extract(url, soup, metadata)
                base_data['custom_field'] = 'custom_value'
                base_data['word_count'] = len(base_data.get('title', '').split())
                return base_data
        
        soup = BeautifulSoup(sample_html_pages['home'], 'html.parser')
        mock_web_scraper.get_page.return_value = soup
        mock_web_scraper.extract_links.return_value = []
        
        with patch('scraper.api.scraper_api.WebScraper', return_value=mock_web_scraper):
            api = ScraperAPI(delay=0, timeout=10)
            
            custom_extractor = CustomExtractor()
            api.set_custom_extractor(custom_extractor)
            
            results = api.crawl_site('https://example.com', max_pages=1)
            
            assert len(results['data']) >= 1
            for data_item in results['data']:
                assert 'custom_field' in data_item
                assert data_item['custom_field'] == 'custom_value'
                assert 'word_count' in data_item


class TestBatchScraperIntegration:
    
    def test_batch_page_scraping_workflow(self):
        urls = [
            'https://example1.com',
            'https://example2.com',
            'https://example3.com'
        ]
        
        with patch('scraper.api.batch_scraper.WebScraper') as mock_scraper_class, \
             patch('scraper.api.batch_scraper.BasicExtractor') as mock_extractor_class, \
             patch('scraper.api.batch_scraper.WebCrawler') as mock_crawler_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_extractor = Mock(spec=BasicExtractor)
            mock_crawler = Mock(spec=WebCrawler)
            
            mock_scraper_class.return_value = mock_scraper
            mock_extractor_class.return_value = mock_extractor
            mock_crawler_class.return_value = mock_crawler
            
            soup = BeautifulSoup('<html><title>Test Page</title></html>', 'html.parser')
            mock_scraper.get_page.return_value = soup
            mock_extractor.extract.return_value = {'url': 'test', 'title': 'Test Page'}
            
            batch_scraper = BatchScraper(delay=0, timeout=10, max_workers=2)
            results = batch_scraper.scrape_multiple_pages(urls)
            
            assert len(results) == 3
            for url in urls:
                assert url in results
                assert results[url]['status'] == 'success'
                assert 'data' in results[url]
            
            combined = batch_scraper.get_combined_results(results)
            assert combined['summary']['total_sites'] == 3
            assert combined['summary']['successful_sites'] == 3
            assert combined['summary']['failed_sites'] == 0
            assert len(combined['all_data']) == 3
    
    def test_batch_site_crawling_workflow(self):
        sites = [
            {'url': 'https://example1.com', 'max_pages': 3},
            {'url': 'https://example2.com', 'max_pages': 5},
            {'url': 'https://example3.com', 'max_pages': 2}
        ]
        
        with patch('scraper.api.batch_scraper.WebScraper') as mock_scraper_class, \
             patch('scraper.api.batch_scraper.BasicExtractor') as mock_extractor_class, \
             patch('scraper.api.batch_scraper.WebCrawler') as mock_crawler_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_extractor = Mock(spec=BasicExtractor)
            mock_crawler = Mock(spec=WebCrawler)
            
            mock_scraper_class.return_value = mock_scraper
            mock_extractor_class.return_value = mock_extractor
            mock_crawler_class.return_value = mock_crawler
            
            crawl_results = {
                'urls': ['https://example.com'],
                'data': [{'url': 'https://example.com', 'title': 'Test Page'}],
                'stats': {'visited_count': 1, 'data_count': 1}
            }
            mock_crawler.crawl.return_value = crawl_results
            
            batch_scraper = BatchScraper(delay=0, timeout=10, max_workers=2)
            results = batch_scraper.crawl_multiple_sites(sites, 'basic')
            
            assert len(results) == 3
            for site in sites:
                assert site['url'] in results
                assert results[site['url']]['status'] == 'success'
                assert 'results' in results[site['url']]
    
    def test_batch_save_workflow(self):
        batch_results = {
            'https://site1.com': {
                'results': {
                    'stats': {'visited_count': 2, 'data_count': 2},
                    'data': [
                        {'url': 'https://site1.com/page1', 'title': 'Page 1'},
                        {'url': 'https://site1.com/page2', 'title': 'Page 2'}
                    ]
                }
            },
            'https://site2.com': {
                'results': {
                    'stats': {'visited_count': 1, 'data_count': 1},
                    'data': [{'url': 'https://site2.com/page1', 'title': 'Page 1'}]
                }
            }
        }
        
        with patch('scraper.api.batch_scraper.save_to_json') as mock_save_json, \
             patch('scraper.api.batch_scraper.save_to_csv') as mock_save_csv:
            
            batch_scraper = BatchScraper()
            
            json_success = batch_scraper.save_batch_results(batch_results, 'batch_test', 'json')
            assert json_success is True
            assert mock_save_json.call_count == 2
            
            csv_success = batch_scraper.save_batch_results(batch_results, 'batch_test', 'csv')
            assert csv_success is True
            assert mock_save_csv.call_count == 3


class TestRAGScraperIntegration:
    
    @pytest.fixture
    def sample_structured_html(self):
        return """
        <html>
            <head><title>Technical Documentation</title></head>
            <body>
                <main>
                    <h1>Python Programming Guide</h1>
                    <h2>Introduction</h2>
                    <p>Python is a versatile programming language.</p>
                    <p>It's great for beginners and experts alike.</p>
                    
                    <h2>Basic Syntax</h2>
                    <p>Here are the basics of Python syntax.</p>
                    <pre>
def hello_world():
    print("Hello, World!")
                    </pre>
                    
                    <h3>Variables</h3>
                    <p>Variables in Python are dynamically typed.</p>
                    
                    <h2>Advanced Topics</h2>
                    <p>Advanced Python concepts include decorators and generators.</p>
                    <ul>
                        <li>Decorators</li>
                        <li>Generators</li>
                        <li>Context Managers</li>
                    </ul>
                </main>
            </body>
        </html>
        """
    
    def test_rag_extraction_workflow(self, sample_structured_html):
        with patch('scraper.api.rag_scraper.WebScraper') as mock_scraper_class, \
             patch('scraper.api.rag_scraper.RAGExtractor') as mock_extractor_class, \
             patch('scraper.api.rag_scraper.WebCrawler') as mock_crawler_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_extractor = Mock(spec=RAGExtractor)
            mock_crawler = Mock(spec=WebCrawler)
            
            mock_scraper_class.return_value = mock_scraper
            mock_extractor_class.return_value = mock_extractor
            mock_crawler_class.return_value = mock_crawler
            
            soup = BeautifulSoup(sample_structured_html, 'html.parser')
            mock_scraper.get_page.return_value = soup
            
            mock_chunks = [
                {
                    'text': 'Python is a versatile programming language. It\'s great for beginners and experts alike.',
                    'title': 'Python Programming Guide > Introduction',
                    'h1': 'Python Programming Guide',
                    'h2': 'Introduction',
                    'h3': '',
                    'url': 'https://example.com/docs',
                    'char_count': 100,
                    'chunk_id': 'chunk1'
                },
                {
                    'text': 'Here are the basics of Python syntax. [CODE]\ndef hello_world():\n    print("Hello, World!")\n[/CODE]',
                    'title': 'Python Programming Guide > Basic Syntax',
                    'h1': 'Python Programming Guide',
                    'h2': 'Basic Syntax',
                    'h3': '',
                    'url': 'https://example.com/docs',
                    'char_count': 120,
                    'chunk_id': 'chunk2'
                },
                {
                    'text': 'Variables in Python are dynamically typed.',
                    'title': 'Python Programming Guide > Basic Syntax > Variables',
                    'h1': 'Python Programming Guide',
                    'h2': 'Basic Syntax',
                    'h3': 'Variables',
                    'url': 'https://example.com/docs',
                    'char_count': 50,
                    'chunk_id': 'chunk3'
                }
            ]
            mock_extractor.extract.return_value = mock_chunks
            mock_crawler.get_collected_data.return_value = mock_chunks
            
            rag_scraper = RAGScraper(chunk_size=200, delay=0, timeout=10)
            
            chunks = rag_scraper.extract_from_page('https://example.com/docs')
            assert len(chunks) == 3
            assert chunks[0]['title'] == 'Python Programming Guide > Introduction'
            assert '[CODE]' in chunks[1]['text']
            
            crawl_results = rag_scraper.crawl_for_rag('https://example.com/docs', max_pages=1)
            assert 'rag_stats' in crawl_results
            assert crawl_results['rag_stats']['total_chunks'] == 3
            
            all_chunks = rag_scraper.get_chunks()
            assert len(all_chunks) == 3
            
            python_chunks = rag_scraper.get_chunks_by_topic('python')
            assert len(python_chunks) == 3
            
            syntax_chunks = rag_scraper.get_chunks_by_topic('syntax')
            assert len(syntax_chunks) == 2
            
            stats = rag_scraper.get_chunk_statistics()
            assert stats['total_chunks'] == 3
            assert stats['unique_pages'] == 1
            assert stats['chunks_with_h1'] == 3
            assert stats['chunks_with_h2'] == 3
            assert stats['chunks_with_h3'] == 1
    
    def test_rag_framework_export_workflow(self, sample_structured_html):
        with patch('scraper.api.rag_scraper.WebScraper') as mock_scraper_class, \
             patch('scraper.api.rag_scraper.RAGExtractor') as mock_extractor_class, \
             patch('scraper.api.rag_scraper.WebCrawler') as mock_crawler_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_extractor = Mock(spec=RAGExtractor)
            mock_crawler = Mock(spec=WebCrawler)
            
            mock_scraper_class.return_value = mock_scraper
            mock_extractor_class.return_value = mock_extractor
            mock_crawler_class.return_value = mock_crawler
            
            mock_chunks = [
                {
                    'text': 'Test content',
                    'title': 'Test Title',
                    'h1': 'Main Topic',
                    'h2': 'Section',
                    'h3': '',
                    'url': 'https://example.com',
                    'char_count': 50,
                    'chunk_id': 'chunk1'
                }
            ]
            mock_crawler.get_collected_data.return_value = mock_chunks
            
            rag_scraper = RAGScraper()
            rag_scraper.crawl_for_rag('https://example.com', max_pages=1)
            
            langchain_chunks = rag_scraper.export_for_rag_framework('langchain')
            assert len(langchain_chunks) == 1
            assert 'page_content' in langchain_chunks[0]
            assert 'metadata' in langchain_chunks[0]
            assert langchain_chunks[0]['metadata']['source'] == 'https://example.com'
            
            llamaindex_chunks = rag_scraper.export_for_rag_framework('llamaindex')
            assert len(llamaindex_chunks) == 1
            assert 'text' in llamaindex_chunks[0]
            assert 'metadata' in llamaindex_chunks[0]
            assert llamaindex_chunks[0]['metadata']['url'] == 'https://example.com'
            
            generic_chunks = rag_scraper.export_for_rag_framework('generic')
            assert generic_chunks == mock_chunks


class TestEndToEndWorkflows:
    
    def test_complete_scraping_pipeline(self):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class, \
             patch('scraper.api.batch_scraper.WebScraper') as mock_batch_scraper_class, \
             patch('scraper.api.rag_scraper.WebScraper') as mock_rag_scraper_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_scraper_class.return_value = mock_scraper
            mock_batch_scraper_class.return_value = mock_scraper
            mock_rag_scraper_class.return_value = mock_scraper
            
            soup = BeautifulSoup('<html><title>Test Page</title><body><h1>Content</h1></body></html>', 'html.parser')
            mock_scraper.get_page.return_value = soup
            mock_scraper.extract_links.return_value = []
            
            api = ScraperAPI(delay=0, timeout=10)
            page_result = api.scrape_page('https://example.com')
            assert page_result is not None
            assert page_result['title'] == 'Test Page'
            
            batch_scraper = BatchScraper(delay=0, timeout=10, max_workers=2)
            batch_results = batch_scraper.scrape_multiple_pages(['https://example1.com', 'https://example2.com'])
            assert len(batch_results) == 2
            
            rag_scraper = RAGScraper(chunk_size=200, delay=0, timeout=10)
            chunks = rag_scraper.extract_from_page('https://example.com')
    
    def test_error_handling_workflow(self):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class:
            mock_scraper = Mock(spec=WebScraper)
            mock_scraper.get_page.return_value = None
            mock_scraper_class.return_value = mock_scraper
            
            api = ScraperAPI(delay=0, timeout=10)
            result = api.scrape_page('https://example.com')
            assert result is None
            
            crawl_result = api.crawl_site('https://example.com', max_pages=1)
            assert crawl_result['stats']['visited_count'] == 1
            assert len(crawl_result['data']) == 0
    
    def test_memory_management_workflow(self):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class:
            mock_scraper = Mock(spec=WebScraper)
            mock_scraper_class.return_value = mock_scraper
            
            with ScraperAPI(delay=0, timeout=10) as api:
                api.scrape_page('https://example.com')
            
            mock_scraper.close.assert_called_once()
            
            api = ScraperAPI(delay=0, timeout=10)
            api.scrape_page('https://example.com')
            api.close()
            
            assert mock_scraper.close.call_count == 2
