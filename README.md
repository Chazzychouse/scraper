# Web Scraper Utility

A comprehensive Python web scraping utility built with BeautifulSoup, Selenium, and other popular scraping libraries. This package provides a modular, extensible framework for web scraping with support for RAG (Retrieval-Augmented Generation) extraction, batch processing, and advanced crawling capabilities.

## Features

- **Multiple Scraping Approaches**: BeautifulSoup-based HTML parsing and Selenium browser automation
- **RAG Integration**: Built-in support for Retrieval-Augmented Generation data extraction
- **Batch Processing**: Parallel processing capabilities for large-scale scraping operations
- **Advanced Crawling**: Multi-threaded web crawling with depth control and domain filtering
- **Flexible Configuration**: Environment variables and programmatic configuration
- **Multiple Output Formats**: JSON, CSV, and custom data formats
- **Rate Limiting**: Built-in request throttling and error handling
- **Extensible Architecture**: Plugin-based extractors and modular design
- **Comprehensive Testing**: Full test suite with coverage reporting

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone <repository-url>
cd scraper

# Install in development mode
pip install -e .
```

### From PyPI (Production)

```bash
pip install web-scraper-utility
```

## Project Structure

```
scraper/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── api/                     # High-level API interfaces
│   ├── scraper_api.py       # Main API interface
│   ├── rag_scraper.py       # RAG-specific scraping
│   └── batch_scraper.py     # Batch processing API
├── core/                    # Core scraping functionality
│   ├── scraper.py           # Base web scraper
│   └── crawler.py           # Multi-threaded crawler
├── extractors/              # Data extraction modules
│   ├── base.py              # Base extractor class
│   ├── basic.py             # Basic HTML extraction
│   └── rag.py               # RAG-specific extraction
└── utils/                   # Utility functions
    ├── data_save.py         # Data saving utilities
    └── url_filter.py        # URL filtering and validation
```

## Quick Start

### Basic Web Scraping

```python
from scraper.api import ScraperAPI
from scraper.core import WebScraper

# Using the high-level API
api = ScraperAPI()
data = api.scrape_url("https://example.com")

# Using the core scraper directly
scraper = WebScraper()
soup = scraper.get_page("https://example.com")
if soup:
    text = scraper.extract_text(soup)
    links = scraper.extract_links(soup, "https://example.com")
scraper.close()
```

### RAG-based Extraction

```python
from scraper.api import RAGScraper

# Initialize RAG scraper
rag_scraper = RAGScraper()

# Extract structured data using RAG
data = rag_scraper.extract_data("https://example.com", 
                                query="Extract product information")
```

### Batch Processing

```python
from scraper.api import BatchScraper

# Process multiple URLs in parallel
urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
batch_scraper = BatchScraper(max_workers=3)
results = batch_scraper.scrape_urls(urls)
```

### Advanced Crawling

```python
from scraper.core import WebCrawler

# Multi-threaded crawling
crawler = WebCrawler(max_pages=50, max_depth=3)
crawler.crawl("https://example.com")
results = crawler.get_results()
```

## Configuration

The scraper uses a centralized configuration system that supports environment variables, programmatic configuration, and validation.

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Request settings
SCRAPER_DELAY=1.0                    # Delay between requests (seconds)
SCRAPER_TIMEOUT=10                   # Request timeout (seconds)
SCRAPER_USER_AGENT=Mozilla/5.0...    # User agent string

# Rate limiting
SCRAPER_MAX_REQUESTS_PER_MINUTE=60   # Rate limiting

# Output settings
SCRAPER_OUTPUT_DIR=output            # Output directory for saved data

# Logging
SCRAPER_LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Crawling settings
SCRAPER_MAX_PAGES=50                 # Default max pages to crawl
SCRAPER_MAX_DEPTH=                   # Max crawl depth (optional)
SCRAPER_STAY_WITHIN_DOMAIN=true      # Stay within same domain

# RAG settings
SCRAPER_CHUNK_SIZE=500               # Target chunk size for RAG extraction

# Batch processing
SCRAPER_MAX_WORKERS=3                # Max parallel workers for batch operations
```

### Programmatic Configuration

```python
from scraper.config import ScraperConfig, get_config, set_config
from scraper.api import ScraperAPI

# Create custom configuration
config = ScraperConfig(
    delay=2.0,
    timeout=15,
    max_pages=100,
    log_level="DEBUG"
)

# Use with API
api = ScraperAPI(config=config)

# Or set as global configuration
set_config(config)
api = ScraperAPI()  # Uses global config
```

### Configuration Features

- **Validation**: All configuration values are validated for correctness
- **Defaults**: Sensible defaults for all settings
- **Flexibility**: Override any setting programmatically or via environment
- **Consistency**: All API classes use the same configuration system
- **Type Safety**: Proper type hints and validation

## Dependencies

### Core Dependencies
- `beautifulsoup4==4.14.2`: HTML parsing and DOM manipulation
- `requests==2.32.5`: HTTP client library
- `lxml==6.0.2`: Fast XML/HTML parser
- `selenium==4.38.0`: Browser automation for JavaScript-heavy sites
- `pandas==2.3.3`: Data manipulation and analysis
- `numpy==2.3.4`: Numerical computing
- `python-dotenv==1.1.1`: Environment variable management

### Development Dependencies
- `pytest==8.4.2`: Testing framework
- `pytest-cov==7.0.0`: Coverage reporting
- `pytest-mock==3.15.1`: Mocking utilities
- `requests-mock==1.12.1`: HTTP request mocking

## Testing

The project includes comprehensive tests with coverage reporting:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scraper --cov-report=html

# Run specific test modules
pytest tests/test_api.py
pytest tests/test_crawler.py
```

Test coverage reports are generated in `.artifacts/htmlcov/` directory.

## Using as a Dependency

### In Your Project

Once installed, you can import and use the scraper in your projects:

```python
# In your project's requirements.txt
web-scraper-utility==1.0.0

# In your Python code
from scraper.api import ScraperAPI, RAGScraper, BatchScraper
from scraper.core import WebScraper, WebCrawler
from scraper.extractors import BasicExtractor, RAGExtractor
from scraper.utils import save_to_json, save_to_csv
```

### Service Integration

Perfect for building web scraping services:

```python
from scraper.api import ScraperAPI
from flask import Flask, jsonify

app = Flask(__name__)
scraper_api = ScraperAPI()

@app.route('/scrape', methods=['POST'])
def scrape_endpoint():
    url = request.json.get('url')
    data = scraper_api.scrape_url(url)
    return jsonify(data)
```

## Output Formats

The scraper supports multiple output formats:

- **JSON**: Structured data export
- **CSV**: Tabular data for analysis
- **Raw Text**: Cleaned text extraction
- **Custom**: Extensible via utility functions

```python
from scraper.utils import save_to_json, save_to_csv

# Save scraped data
save_to_json(data, 'output/scraped_data.json')
save_to_csv(data, 'output/scraped_data.csv')
```

## Best Practices

1. **Respect Website Policies**: Always check robots.txt and terms of service
2. **Rate Limiting**: Use appropriate delays between requests
3. **Error Handling**: Implement robust error handling and retry logic
4. **Monitoring**: Log scraping activity and monitor for issues
5. **Resource Management**: Use connection pooling and proper cleanup
6. **Legal Compliance**: Ensure compliance with data protection laws
7. **Testing**: Test your scraping logic thoroughly before production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is open source. Please use responsibly and in accordance with website terms of service and applicable laws.
