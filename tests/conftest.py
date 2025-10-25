import pytest
from unittest.mock import Mock
from scraper.core.scraper import WebScraper
from scraper.core.crawler import WebCrawler
from scraper.extractors.basic import BasicExtractor
from scraper.extractors.rag import RAGExtractor

@pytest.fixture
def scraper():
    scraper = WebScraper(delay=0)
    yield scraper
    scraper.close()

@pytest.fixture
def core_scraper():
    scraper = WebScraper(delay=0, timeout=10)
    yield scraper
    scraper.close()

@pytest.fixture
def sample_html():
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello World</h1>
            <a href="/page1">Link 1</a>
            <a href="https://example.com/page2">Link 2</a>
            <p class="content">Test content here</p>
        </body>
    </html>
    """

@pytest.fixture
def sample_html_with_structure():
    return """
    <html>
        <head><title>Documentation Page</title></head>
        <body>
            <main>
                <h1>Main Topic</h1>
                <h2>Section 1</h2>
                <p>This is section 1 content with some detailed information.</p>
                <p>This is additional content in the same section.</p>
                
                <h2>Section 2</h2>
                <p>This is section 2 content with different information.</p>
                <ul>
                    <li>First item</li>
                    <li>Second item</li>
                </ul>
                
                <h3>Subsection 2.1</h3>
                <p>This is a subsection with more detailed information.</p>
                <pre>
def example_function():
    return "Hello World"
                </pre>
            </main>
        </body>
    </html>
    """

@pytest.fixture
def mock_scraper():
    return Mock(spec=WebScraper)

@pytest.fixture
def mock_extractor():
    return Mock(spec=BasicExtractor)

@pytest.fixture
def mock_rag_extractor():
    return Mock(spec=RAGExtractor)

@pytest.fixture
def mock_crawler():
    return Mock(spec=WebCrawler)

@pytest.fixture
def basic_extractor():
    return BasicExtractor()

@pytest.fixture
def rag_extractor():
    return RAGExtractor(chunk_size_target=200)

@pytest.fixture
def crawler_with_mocks(mock_scraper, mock_extractor):
    return WebCrawler(mock_scraper, mock_extractor)

@pytest.fixture
def sample_crawl_data():
    return {
        'urls': ['https://example.com', 'https://example.com/page1'],
        'data': [
            {'url': 'https://example.com', 'title': 'Home Page', 'text_length': 100, 'link_count': 5, 'depth': 0},
            {'url': 'https://example.com/page1', 'title': 'Page 1', 'text_length': 150, 'link_count': 3, 'depth': 1}
        ],
        'stats': {
            'visited_count': 2,
            'queued_count': 0,
            'collected_count': 2,
            'data_count': 2
        }
    }

@pytest.fixture
def sample_rag_chunks():
    return [
        {
            'text': 'This is section 1 content with some detailed information.',
            'title': 'Main Topic > Section 1',
            'page_title': 'Documentation Page',
            'h1': 'Main Topic',
            'h2': 'Section 1',
            'h3': '',
            'url': 'https://example.com/docs',
            'source': 'https://example.com/docs',
            'depth': 0,
            'char_count': 60,
            'chunk_id': 'https://example.com/docs#Main-Topic-Section-1'
        },
        {
            'text': 'This is section 2 content with different information.',
            'title': 'Main Topic > Section 2',
            'page_title': 'Documentation Page',
            'h1': 'Main Topic',
            'h2': 'Section 2',
            'h3': '',
            'url': 'https://example.com/docs',
            'source': 'https://example.com/docs',
            'depth': 0,
            'char_count': 55,
            'chunk_id': 'https://example.com/docs#Main-Topic-Section-2'
        }
    ]