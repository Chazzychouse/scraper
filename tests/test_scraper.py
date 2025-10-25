import requests
from bs4 import BeautifulSoup
from scraper.core.scraper import WebScraper
from scraper.config import get_config

class TestWebScraperInit:
    def test_default_initialization(self):
        scraper = WebScraper()
        config = get_config()
        assert scraper.delay == config.delay
        assert scraper.timeout == config.timeout
        scraper.close()
    
    def test_custom_delay(self):
        scraper = WebScraper(delay=2.0)
        assert scraper.delay == 2.0
        scraper.close()
    
    def test_custom_timeout(self):
        scraper = WebScraper(timeout=15)
        assert scraper.timeout == 15
        scraper.close()

class TestGetPage:
    def test_get_page_success(self, scraper, requests_mock, sample_html):
        requests_mock.get("https://example.com", text=sample_html)
        
        soup = scraper.get_page("https://example.com")
        
        assert soup is not None
        assert isinstance(soup, BeautifulSoup)
        assert soup.title.string == "Test Page"
    
    def test_get_page_with_full_url(self, sample_html, requests_mock):
        scraper = WebScraper(delay=0)
        requests_mock.get("https://example.com/test", text=sample_html)
        
        soup = scraper.get_page("https://example.com/test")
        
        assert soup is not None
        assert soup.title.string == "Test Page"
        scraper.close()
    
    def test_get_page_failure(self, scraper, requests_mock):
        requests_mock.get("https://example.com", status_code=404)
        
        soup = scraper.get_page("https://example.com")
        
        assert soup is None
    
    def test_get_page_timeout(self, scraper, requests_mock):
        requests_mock.get("https://example.com", exc=requests.Timeout)
        
        soup = scraper.get_page("https://example.com")
        
        assert soup is None

class TestExtractLinks:
    def test_extract_links(self, scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        links = scraper.extract_links(soup)
        
        assert len(links) == 2
        assert "/page1" in links
        assert "https://example.com/page2" in links
    
    def test_extract_links_with_base_url(self, scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        links = scraper.extract_links(soup, base_url="https://example.com")
        
        assert len(links) == 2
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
    
    def test_extract_links_empty(self, scraper):
        html = "<html><body><p>No links here</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        
        links = scraper.extract_links(soup)
        
        assert len(links) == 0

class TestExtractText:
    def test_extract_text_all(self, scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        text = scraper.extract_text(soup)
        
        assert "Hello World" in text
        assert "Test content here" in text
    
    def test_extract_text_with_selector(self, scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        text = scraper.extract_text(soup, selector=".content")
        
        assert text == "Test content here"
    
    def test_extract_text_no_match(self, scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        text = scraper.extract_text(soup, selector=".nonexistent")
        
        assert text == ""