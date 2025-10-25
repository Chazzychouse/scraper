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


class TestScraperAPI:
    
    @pytest.fixture
    def api(self):
        return ScraperAPI(delay=0, timeout=10)
    
    @pytest.fixture
    def sample_html(self):
        return """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Hello World</h1>
                <p>This is test content</p>
                <a href="/page1">Link 1</a>
                <a href="/page2">Link 2</a>
            </body>
        </html>
        """
    
    def test_initialization(self):
        api = ScraperAPI(delay=1.0, timeout=30)
        
        assert api.delay == 1.0
        assert api.timeout == 30
        assert api._scraper is None
        assert api._crawler is None
        assert api._extractor is None
    
    def test_scrape_page_success(self, api, sample_html):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class:
            mock_scraper = Mock(spec=WebScraper)
            mock_scraper_class.return_value = mock_scraper
            
            soup = BeautifulSoup(sample_html, 'html.parser')
            mock_scraper.get_page.return_value = soup
            
            result = api.scrape_page('https://example.com')
            
            assert result is not None
            assert result['url'] == 'https://example.com'
            assert result['title'] == 'Test Page'
            assert result['text_length'] > 0
            assert result['link_count'] == 2
            assert result['status'] == 'success'
            
            mock_scraper.get_page.assert_called_once_with('https://example.com')
    
    def test_scrape_page_failure(self, api):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class:
            mock_scraper = Mock(spec=WebScraper)
            mock_scraper_class.return_value = mock_scraper
            mock_scraper.get_page.return_value = None
            
            result = api.scrape_page('https://example.com')
            
            assert result is None
    
    def test_crawl_site_success(self, api, sample_html):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class, \
             patch('scraper.api.scraper_api.WebCrawler') as mock_crawler_class, \
             patch('scraper.api.scraper_api.BasicExtractor') as mock_extractor_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_crawler = Mock(spec=WebCrawler)
            mock_extractor = Mock(spec=BasicExtractor)
            
            mock_scraper_class.return_value = mock_scraper
            mock_crawler_class.return_value = mock_crawler
            mock_extractor_class.return_value = mock_extractor
            
            crawl_results = {
                'urls': ['https://example.com', 'https://example.com/page1'],
                'data': [{'url': 'https://example.com', 'title': 'Test Page'}],
                'stats': {'visited_count': 2, 'data_count': 1}
            }
            mock_crawler.crawl.return_value = crawl_results
            
            result = api.crawl_site('https://example.com', max_pages=10)
            
            assert result == crawl_results
            mock_crawler.crawl.assert_called_once_with(
                start_url='https://example.com',
                max_pages=10,
                max_depth=None,
                stay_within_domain=True,
                url_filter=None
            )
    
    def test_get_url_statistics_no_crawl(self, api):
        result = api.get_url_statistics()
        
        assert result == {'error': 'No crawl performed yet'}
    
    def test_get_url_statistics_with_crawl(self, api):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class, \
             patch('scraper.api.scraper_api.WebCrawler') as mock_crawler_class, \
             patch('scraper.api.scraper_api.BasicExtractor') as mock_extractor_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_crawler = Mock(spec=WebCrawler)
            mock_extractor = Mock(spec=BasicExtractor)
            
            mock_scraper_class.return_value = mock_scraper
            mock_crawler_class.return_value = mock_crawler
            mock_extractor_class.return_value = mock_extractor
            
            url_stats = {
                'total_urls': 10,
                'visited_urls': 5,
                'queued_urls': 5
            }
            mock_crawler.get_url_statistics.return_value = url_stats
            
            api.crawl_site('https://example.com', max_pages=5)
            
            result = api.get_url_statistics()
            
            assert result == url_stats
    
    def test_get_all_urls_no_crawl(self, api):
        result = api.get_all_urls()
        
        assert result == []
    
    def test_get_visited_urls_no_crawl(self, api):
        result = api.get_visited_urls()
        
        assert result == []
    
    def test_save_results_no_crawl(self, api):
        result = api.save_results('test', 'json')
        
        assert result is False
    
    def test_save_results_success(self, api):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class, \
             patch('scraper.api.scraper_api.WebCrawler') as mock_crawler_class, \
             patch('scraper.api.scraper_api.BasicExtractor') as mock_extractor_class, \
             patch('scraper.api.scraper_api.save_to_json') as mock_save_json:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_crawler = Mock(spec=WebCrawler)
            mock_extractor = Mock(spec=BasicExtractor)
            
            mock_scraper_class.return_value = mock_scraper
            mock_crawler_class.return_value = mock_crawler
            mock_extractor_class.return_value = mock_extractor
            
            mock_crawler.get_collected_data.return_value = [{'url': 'https://example.com', 'title': 'Test'}]
            
            api.crawl_site('https://example.com', max_pages=1)
            
            result = api.save_results('test', 'json')
            
            assert result is True
            mock_save_json.assert_called_once()
    
    def test_set_custom_extractor(self, api):
        custom_extractor = Mock(spec=BasicExtractor)
        
        api.set_custom_extractor(custom_extractor)
        
        assert api._extractor == custom_extractor
    
    def test_context_manager(self, api):
        with patch('scraper.api.scraper_api.WebScraper') as mock_scraper_class:
            mock_scraper = Mock(spec=WebScraper)
            mock_scraper_class.return_value = mock_scraper
            
            with api as context_api:
                assert context_api is api
                context_api.scrape_page('https://example.com')
            
            mock_scraper.close.assert_called_once()


class TestBatchScraper:
    
    @pytest.fixture
    def batch_scraper(self):
        return BatchScraper(delay=0, timeout=10, max_workers=2)
    
    def test_initialization(self):
        batch = BatchScraper(delay=1.0, timeout=30, max_workers=5)
        
        assert batch.delay == 1.0
        assert batch.timeout == 30
        assert batch.max_workers == 5
        assert batch._results == {}
    
    def test_scrape_multiple_pages(self, batch_scraper):
        urls = ['https://example.com/page1', 'https://example.com/page2']
        
        with patch('scraper.api.batch_scraper.WebScraper') as mock_scraper_class, \
             patch('scraper.api.batch_scraper.BasicExtractor') as mock_extractor_class, \
             patch('scraper.api.batch_scraper.WebCrawler') as mock_crawler_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_extractor = Mock(spec=BasicExtractor)
            mock_crawler = Mock(spec=WebCrawler)
            
            mock_scraper_class.return_value = mock_scraper
            mock_extractor_class.return_value = mock_extractor
            mock_crawler_class.return_value = mock_crawler
            
            soup = BeautifulSoup('<html><title>Test</title></html>', 'html.parser')
            mock_scraper.get_page.return_value = soup
            mock_extractor.extract.return_value = {'url': 'test', 'title': 'Test'}
            
            results = batch_scraper.scrape_multiple_pages(urls)
            
            assert len(results) == 2
            for url in urls:
                assert url in results
                assert results[url]['status'] == 'success'
                assert 'data' in results[url]
    
    def test_crawl_multiple_sites(self, batch_scraper):
        sites = [
            {'url': 'https://example1.com', 'max_pages': 5},
            {'url': 'https://example2.com', 'max_pages': 10}
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
                'data': [{'url': 'https://example.com', 'title': 'Test'}],
                'stats': {'visited_count': 1, 'data_count': 1}
            }
            mock_crawler.crawl.return_value = crawl_results
            
            results = batch_scraper.crawl_multiple_sites(sites, 'basic')
            
            assert len(results) == 2
            for site in sites:
                assert site['url'] in results
                assert results[site['url']]['status'] == 'success'
                assert 'results' in results[site['url']]
    
    def test_get_combined_results(self, batch_scraper):
        batch_results = {
            'https://site1.com': {
                'results': {
                    'stats': {'visited_count': 5, 'data_count': 5},
                    'data': [{'url': 'site1', 'title': 'Page 1'}]
                }
            },
            'https://site2.com': {
                'error': 'Failed to crawl'
            },
            'https://site3.com': {
                'data': {'url': 'site3', 'title': 'Single Page'}
            }
        }
        
        combined = batch_scraper.get_combined_results(batch_results)
        
        assert combined['summary']['total_sites'] == 3
        assert combined['summary']['successful_sites'] == 2
        assert combined['summary']['failed_sites'] == 1
        assert combined['summary']['total_pages'] == 6
        assert combined['summary']['total_data_entries'] == 6
        assert len(combined['all_data']) == 6
        assert combined['site_results'] == batch_results
    
    def test_create_site_configs(self, batch_scraper):
        urls = ['https://example1.com', 'https://example2.com']
        
        configs = batch_scraper.create_site_configs(
            urls, 
            max_pages=20, 
            max_depth=3, 
            stay_within_domain=False
        )
        
        assert len(configs) == 2
        for i, config in enumerate(configs):
            assert config['url'] == urls[i]
            assert config['max_pages'] == 20
            assert config['max_depth'] == 3
            assert config['stay_within_domain'] is False
    
    def test_add_url_filter(self, batch_scraper):
        configs = [
            {'url': 'https://example1.com'},
            {'url': 'https://example2.com'}
        ]
        
        filter_func = lambda url: 'example1' in url
        
        batch_scraper.add_url_filter(configs, filter_func)
        
        for config in configs:
            assert config['url_filter'] == filter_func


class TestRAGScraper:
    
    @pytest.fixture
    def rag_scraper(self):
        return RAGScraper(chunk_size=300, delay=0, timeout=10)
    
    @pytest.fixture
    def sample_html_with_structure(self):
        return """
        <html>
            <head><title>Documentation</title></head>
            <body>
                <main>
                    <h1>Main Topic</h1>
                    <h2>Section 1</h2>
                    <p>This is section 1 content.</p>
                    <h2>Section 2</h2>
                    <p>This is section 2 content.</p>
                </main>
            </body>
        </html>
        """
    
    def test_initialization(self):
        rag = RAGScraper(chunk_size=500, delay=1.0, timeout=30)
        
        assert rag.chunk_size == 500
        assert rag.delay == 1.0
        assert rag.timeout == 30
        assert rag._scraper is None
        assert rag._crawler is None
        assert rag._extractor is None
    
    def test_extract_from_page_success(self, rag_scraper, sample_html_with_structure):
        with patch('scraper.api.rag_scraper.WebScraper') as mock_scraper_class, \
             patch('scraper.api.rag_scraper.RAGExtractor') as mock_extractor_class, \
             patch('scraper.api.rag_scraper.WebCrawler') as mock_crawler_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_extractor = Mock(spec=RAGExtractor)
            mock_crawler = Mock(spec=WebCrawler)
            
            mock_scraper_class.return_value = mock_scraper
            mock_extractor_class.return_value = mock_extractor
            mock_crawler_class.return_value = mock_crawler
            
            soup = BeautifulSoup(sample_html_with_structure, 'html.parser')
            mock_scraper.get_page.return_value = soup
            
            mock_chunks = [
                {'text': 'Section 1 content', 'title': 'Main Topic > Section 1', 'url': 'https://example.com'},
                {'text': 'Section 2 content', 'title': 'Main Topic > Section 2', 'url': 'https://example.com'}
            ]
            mock_extractor.extract.return_value = mock_chunks
            
            chunks = rag_scraper.extract_from_page('https://example.com')
            
            assert chunks == mock_chunks
            mock_scraper.get_page.assert_called_once_with('https://example.com')
            mock_extractor.extract.assert_called_once()
    
    def test_extract_from_page_failure(self, rag_scraper):
        with patch('scraper.api.rag_scraper.WebScraper') as mock_scraper_class, \
             patch('scraper.api.rag_scraper.RAGExtractor') as mock_extractor_class, \
             patch('scraper.api.rag_scraper.WebCrawler') as mock_crawler_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_extractor = Mock(spec=RAGExtractor)
            mock_crawler = Mock(spec=WebCrawler)
            
            mock_scraper_class.return_value = mock_scraper
            mock_extractor_class.return_value = mock_extractor
            mock_crawler_class.return_value = mock_crawler
            
            mock_scraper.get_page.return_value = None
            
            chunks = rag_scraper.extract_from_page('https://example.com')
            
            assert chunks == []
    
    def test_crawl_for_rag_success(self, rag_scraper, sample_html_with_structure):
        with patch('scraper.api.rag_scraper.WebScraper') as mock_scraper_class, \
             patch('scraper.api.rag_scraper.RAGExtractor') as mock_extractor_class, \
             patch('scraper.api.rag_scraper.WebCrawler') as mock_crawler_class:
            
            mock_scraper = Mock(spec=WebScraper)
            mock_extractor = Mock(spec=RAGExtractor)
            mock_crawler = Mock(spec=WebCrawler)
            
            mock_scraper_class.return_value = mock_scraper
            mock_extractor_class.return_value = mock_extractor
            mock_crawler_class.return_value = mock_crawler
            
            crawl_results = {
                'urls': ['https://example.com'],
                'data': [
                    {'text': 'Content 1', 'char_count': 100, 'url': 'https://example.com'},
                    {'text': 'Content 2', 'char_count': 200, 'url': 'https://example.com'}
                ],
                'stats': {'visited_count': 1, 'data_count': 2}
            }
            mock_crawler.crawl.return_value = crawl_results
            
            results = rag_scraper.crawl_for_rag('https://example.com', max_pages=5)
            
            assert 'rag_stats' in results
            assert results['rag_stats']['total_chunks'] == 2
            assert results['rag_stats']['avg_chunk_size'] == 150.0
            assert results['rag_stats']['min_chunk_size'] == 100
            assert results['rag_stats']['max_chunk_size'] == 200
    
    def test_get_chunks_no_crawl(self, rag_scraper):
        chunks = rag_scraper.get_chunks()
        
        assert chunks == []
    
    def test_get_chunks_by_page(self, rag_scraper):
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
                {'text': 'Content 1', 'url': 'https://example.com/page1'},
                {'text': 'Content 2', 'url': 'https://example.com/page2'}
            ]
            mock_crawler.get_collected_data.return_value = mock_chunks
            
            rag_scraper.crawl_for_rag('https://example.com', max_pages=1)
            
            page1_chunks = rag_scraper.get_chunks_by_page('https://example.com/page1')
            page2_chunks = rag_scraper.get_chunks_by_page('https://example.com/page2')
            page3_chunks = rag_scraper.get_chunks_by_page('https://example.com/page3')
            
            assert len(page1_chunks) == 1
            assert len(page2_chunks) == 1
            assert len(page3_chunks) == 0
    
    def test_get_chunks_by_topic(self, rag_scraper):
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
                {'text': 'This is about Python programming', 'title': 'Python Guide', 'url': 'https://example.com'},
                {'text': 'This is about JavaScript development', 'title': 'JS Guide', 'url': 'https://example.com'},
                {'text': 'This is about data science with Python', 'title': 'Data Science', 'url': 'https://example.com'}
            ]
            mock_crawler.get_collected_data.return_value = mock_chunks
            
            rag_scraper.crawl_for_rag('https://example.com', max_pages=1)
            
            python_chunks = rag_scraper.get_chunks_by_topic('python')
            js_chunks = rag_scraper.get_chunks_by_topic('javascript')
            data_chunks = rag_scraper.get_chunks_by_topic('data science')
            none_chunks = rag_scraper.get_chunks_by_topic('nonexistent')
            
            assert len(python_chunks) == 2
            assert len(js_chunks) == 1
            assert len(data_chunks) == 1
            assert len(none_chunks) == 0
    
    def test_get_chunk_statistics(self, rag_scraper):
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
                    'text': 'Content 1', 'char_count': 100, 'url': 'https://example.com/page1',
                    'h1': 'Main Topic', 'h2': 'Section 1', 'h3': '', 'title': 'Main Topic > Section 1'
                },
                {
                    'text': 'Content 2', 'char_count': 200, 'url': 'https://example.com/page2',
                    'h1': 'Main Topic', 'h2': 'Section 2', 'h3': 'Subsection', 'title': 'Main Topic > Section 2 > Subsection'
                }
            ]
            mock_crawler.get_collected_data.return_value = mock_chunks
            
            rag_scraper.crawl_for_rag('https://example.com', max_pages=1)
            
            stats = rag_scraper.get_chunk_statistics()
            
            assert stats['total_chunks'] == 2
            assert stats['unique_pages'] == 2
            assert stats['avg_chunk_size'] == 150.0
            assert stats['min_chunk_size'] == 100
            assert stats['max_chunk_size'] == 200
            assert stats['chunks_with_h1'] == 2
            assert stats['chunks_with_h2'] == 2
            assert stats['chunks_with_h3'] == 1
    
    def test_get_chunk_statistics_no_chunks(self, rag_scraper):
        stats = rag_scraper.get_chunk_statistics()
        
        assert stats == {'error': 'No chunks available'}
    
    def test_export_for_rag_framework(self, rag_scraper):
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
                    'text': 'Content 1', 'char_count': 100, 'url': 'https://example.com',
                    'h1': 'Main Topic', 'h2': 'Section 1', 'h3': '', 'title': 'Main Topic > Section 1',
                    'chunk_id': 'chunk1'
                }
            ]
            mock_crawler.get_collected_data.return_value = mock_chunks
            
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
    
    def test_context_manager(self, rag_scraper):
        with patch('scraper.api.rag_scraper.WebScraper') as mock_scraper_class:
            mock_scraper = Mock(spec=WebScraper)
            mock_scraper_class.return_value = mock_scraper
            
            with rag_scraper as context_rag:
                assert context_rag is rag_scraper
                context_rag.extract_from_page('https://example.com')
            
            mock_scraper.close.assert_called_once()
