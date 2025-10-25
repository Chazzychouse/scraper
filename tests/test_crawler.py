import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
from scraper.core.crawler import WebCrawler
from scraper.core.scraper import WebScraper
from scraper.extractors.basic import BasicExtractor


class TestWebCrawlerInit:
    
    def test_initialization_with_scraper(self):
        scraper = Mock(spec=WebScraper)
        crawler = WebCrawler(scraper)
        
        assert crawler.scraper == scraper
        assert crawler.extractor is None
        assert crawler.visited_urls == set()
        assert len(crawler.to_visit) == 0
        assert crawler.collected_urls == []
        assert crawler.collected_data == []
    
    def test_initialization_with_scraper_and_extractor(self):
        scraper = Mock(spec=WebScraper)
        extractor = Mock(spec=BasicExtractor)
        crawler = WebCrawler(scraper, extractor)
        
        assert crawler.scraper == scraper
        assert crawler.extractor == extractor


class TestWebCrawlerCrawl:
    
    @pytest.fixture
    def mock_scraper(self):
        scraper = Mock(spec=WebScraper)
        return scraper
    
    @pytest.fixture
    def mock_extractor(self):
        extractor = Mock(spec=BasicExtractor)
        return extractor
    
    @pytest.fixture
    def sample_html(self):
        return """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p>Content here</p>
                <a href="/page1">Link 1</a>
                <a href="/page2">Link 2</a>
                <a href="https://external.com/page">External Link</a>
            </body>
        </html>
        """
    
    def test_crawl_single_page_no_extractor(self, mock_scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        mock_scraper.get_page.return_value = soup
        mock_scraper.extract_links.return_value = ['/page1', '/page2', 'https://external.com/page']
        
        crawler = WebCrawler(mock_scraper)
        
        results = crawler.crawl('https://example.com', max_pages=1)
        
        assert results['stats']['visited_count'] == 1
        assert results['stats']['data_count'] == 0
        assert 'https://example.com' in results['urls']
        assert len(results['data']) == 0
        
        mock_scraper.get_page.assert_called_once_with('https://example.com')
        mock_scraper.extract_links.assert_called_once()
    
    def test_crawl_with_extractor(self, mock_scraper, mock_extractor, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        mock_scraper.get_page.return_value = soup
        mock_scraper.extract_links.return_value = ['/page1', '/page2']
        
        extracted_data = {'url': 'https://example.com', 'title': 'Test Page', 'text_length': 100}
        mock_extractor.extract.return_value = extracted_data
        
        crawler = WebCrawler(mock_scraper, mock_extractor)
        
        results = crawler.crawl('https://example.com', max_pages=1)
        
        assert results['stats']['visited_count'] == 1
        assert results['stats']['data_count'] == 1
        assert extracted_data in results['data']
        
        mock_extractor.extract.assert_called_once()
        call_args = mock_extractor.extract.call_args
        assert call_args[0][0] == 'https://example.com'
        assert call_args[0][1] == soup
        assert call_args[0][2]['depth'] == 0
    
    def test_crawl_with_max_pages_limit(self, mock_scraper, sample_html):
        def mock_get_page(url):
            soup = BeautifulSoup(sample_html, 'html.parser')
            if 'page1' in url:
                soup.title.string = 'Page 1'
            return soup
        
        def mock_extract_links(soup, base_url=None):
            return ['https://example.com/page1', 'https://example.com/page2', 'https://example.com/page3']
        
        mock_scraper.get_page.side_effect = mock_get_page
        mock_scraper.extract_links.side_effect = mock_extract_links
        
        crawler = WebCrawler(mock_scraper)
        
        results = crawler.crawl('https://example.com', max_pages=2)
        
        assert results['stats']['visited_count'] == 2
        assert len(results['urls']) == 2
    
    def test_crawl_with_max_depth_limit(self, mock_scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        mock_scraper.get_page.return_value = soup
        mock_scraper.extract_links.return_value = ['/page1', '/page2']
        
        crawler = WebCrawler(mock_scraper)
        
        results = crawler.crawl('https://example.com', max_depth=1)
        
        assert results['stats']['visited_count'] >= 1
    
    def test_crawl_stay_within_domain(self, mock_scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        mock_scraper.get_page.return_value = soup
        mock_scraper.extract_links.return_value = [
            '/page1', 
            '/page2', 
            'https://external.com/page',
            'https://example.com/page3'
        ]
        
        crawler = WebCrawler(mock_scraper)
        
        results = crawler.crawl('https://example.com', max_pages=5, stay_within_domain=True)
        
        for url in results['urls']:
            assert 'example.com' in url or url.startswith('/')
    
    def test_crawl_with_url_filter(self, mock_scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        mock_scraper.get_page.return_value = soup
        mock_scraper.extract_links.return_value = ['/page1', '/page2', '/filtered']
        
        url_filter = lambda url: 'page1' in url
        
        crawler = WebCrawler(mock_scraper)
        
        results = crawler.crawl('https://example.com', max_pages=5, url_filter=url_filter)
        
        for url in results['urls']:
            if url != 'https://example.com':
                assert 'page1' in url
    
    def test_crawl_invalid_start_url(self, mock_scraper):
        crawler = WebCrawler(mock_scraper)
        
        with pytest.raises(ValueError, match="Invalid start URL"):
            crawler.crawl('not-a-url')
    
    def test_crawl_page_fetch_failure(self, mock_scraper):
        mock_scraper.get_page.return_value = None
        mock_scraper.extract_links.return_value = ['/page1']
        
        crawler = WebCrawler(mock_scraper)
        
        results = crawler.crawl('https://example.com', max_pages=2)
        
        assert results['stats']['visited_count'] == 1
        assert len(results['data']) == 0
    
    def test_crawl_extractor_error(self, mock_scraper, mock_extractor, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        mock_scraper.get_page.return_value = soup
        mock_scraper.extract_links.return_value = []
        
        mock_extractor.extract.side_effect = Exception("Extraction failed")
        
        crawler = WebCrawler(mock_scraper, mock_extractor)
        
        results = crawler.crawl('https://example.com', max_pages=1)
        
        assert results['stats']['visited_count'] == 1
        assert len(results['data']) == 0
        
        mock_extractor.on_extraction_error.assert_called_once()


class TestWebCrawlerUtilityMethods:
    
    @pytest.fixture
    def crawler_with_data(self):
        scraper = Mock(spec=WebScraper)
        crawler = WebCrawler(scraper)
        
        crawler.visited_urls = {'https://example.com', 'https://example.com/page1'}
        crawler.to_visit = [('https://example.com/page2', 1), ('https://example.com/page3', 2)]
        crawler.collected_urls = ['https://example.com', 'https://example.com/page1']
        crawler.collected_data = [{'url': 'https://example.com', 'title': 'Page 1'}]
        
        return crawler
    
    def test_get_results(self, crawler_with_data):
        results = crawler_with_data.get_results()
        
        assert 'urls' in results
        assert 'data' in results
        assert 'stats' in results
        assert results['stats']['visited_count'] == 2
        assert results['stats']['queued_count'] == 2
        assert results['stats']['collected_count'] == 2
        assert results['stats']['data_count'] == 1
    
    def test_get_total_urls(self, crawler_with_data):
        total = crawler_with_data.get_total_urls()
        assert total == 4
    
    def test_get_visited_urls(self, crawler_with_data):
        visited = crawler_with_data.get_visited_urls()
        assert len(visited) == 2
        assert 'https://example.com' in visited
        assert 'https://example.com/page1' in visited
    
    def test_get_queued_urls(self, crawler_with_data):
        queued = crawler_with_data.get_queued_urls()
        assert len(queued) == 2
        assert 'https://example.com/page2' in queued
        assert 'https://example.com/page3' in queued
    
    def test_get_all_discovered_urls(self, crawler_with_data):
        all_urls = crawler_with_data.get_all_discovered_urls()
        assert len(all_urls) == 4
        assert 'https://example.com' in all_urls
        assert 'https://example.com/page1' in all_urls
        assert 'https://example.com/page2' in all_urls
        assert 'https://example.com/page3' in all_urls
    
    def test_get_url_statistics(self, crawler_with_data):
        stats = crawler_with_data.get_url_statistics()
        
        assert stats['total_urls'] == 4
        assert stats['visited_urls'] == 2
        assert stats['queued_urls'] == 2
        assert stats['visited_percentage'] == 50.0
        assert stats['queued_percentage'] == 50.0
    
    def test_get_domain_urls(self, crawler_with_data):
        example_urls = crawler_with_data.get_domain_urls('example.com')
        assert len(example_urls) == 4
        
        external_urls = crawler_with_data.get_domain_urls('external.com')
        assert len(external_urls) == 0
    
    def test_get_urls_by_depth(self, crawler_with_data):
        depth_1_urls = crawler_with_data.get_urls_by_depth(1)
        assert len(depth_1_urls) == 1
        assert 'https://example.com/page2' in depth_1_urls
        
        depth_2_urls = crawler_with_data.get_urls_by_depth(2)
        assert len(depth_2_urls) == 1
        assert 'https://example.com/page3' in depth_2_urls
    
    def test_reset(self):
        scraper = Mock(spec=WebScraper)
        crawler = WebCrawler(scraper)
        
        crawler.visited_urls.add('https://example.com')
        crawler.to_visit.append(('https://example.com/page1', 1))
        crawler.collected_urls.append('https://example.com')
        crawler.collected_data.append({'url': 'https://example.com'})
        
        crawler._reset()
        
        assert len(crawler.visited_urls) == 0
        assert len(crawler.to_visit) == 0
        assert len(crawler.collected_urls) == 0
        assert len(crawler.collected_data) == 0


class TestWebCrawlerShouldVisit:
    
    @pytest.fixture
    def crawler(self):
        scraper = Mock(spec=WebScraper)
        return WebCrawler(scraper)
    
    def test_should_visit_already_visited(self, crawler):
        crawler.visited_urls.add('https://example.com/page1')
        
        result = crawler._should_visit(
            'https://example.com/page1',
            'example.com',
            True,
            None
        )
        
        assert result is False
    
    def test_should_visit_invalid_url(self, crawler):
        result = crawler._should_visit(
            'not-a-url',
            'example.com',
            True,
            None
        )
        
        assert result is False
    
    def test_should_visit_different_domain_stay_within(self, crawler):
        result = crawler._should_visit(
            'https://external.com/page',
            'example.com',
            True,
            None
        )
        
        assert result is False
    
    def test_should_visit_different_domain_allow_external(self, crawler):
        result = crawler._should_visit(
            'https://external.com/page',
            'example.com',
            False,
            None
        )
        
        assert result is True
    
    def test_should_visit_with_url_filter(self, crawler):
        url_filter = lambda url: 'allowed' in url
        
        result = crawler._should_visit(
            'https://example.com/allowed',
            'example.com',
            True,
            url_filter
        )
        assert result is True
        
        result = crawler._should_visit(
            'https://example.com/blocked',
            'example.com',
            True,
            url_filter
        )
        assert result is False
    
    def test_should_visit_valid_url(self, crawler):
        result = crawler._should_visit(
            'https://example.com/page1',
            'example.com',
            True,
            None
        )
        
        assert result is True
