# Web Scraper Utility

A Python web scraping utility built with BeautifulSoup and other popular scraping libraries.

## Features

- BeautifulSoup-based HTML parsing
- Request session management with configurable delays
- Support for multiple output formats (JSON, CSV)
- Configurable settings via environment variables
- Rate limiting and error handling
- Extensible base scraper class

## Project Structure

```
scraper/
├── __init__.py          # Package initialization
├── scraper.py           # Main scraper class
├── config.py            # Configuration settings
└── utils.py             # Utility functions

example.py               # Example usage
requirements.txt         # Python dependencies
.env.example            # Environment variables template
.gitignore              # Git ignore rules
README.md               # This file
```

## Setup

1. **Create a virtual environment:**

   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**

   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## Usage

### Basic Usage

```python
from scraper.scraper import WebScraper

# Initialize scraper
scraper = WebScraper(delay=1.0)

# Fetch a page
soup = scraper.get_page("https://example.com")

if soup:
    # Extract text
    text = scraper.extract_text(soup)

    # Extract links
    links = scraper.extract_links(soup, "https://example.com")

# Clean up
scraper.close()
```

### Running the Example

```bash
python example.py
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

- `beautifulsoup4`: HTML parsing
- `requests`: HTTP requests
- `lxml`: XML/HTML parser
- `selenium`: Browser automation (optional)
- `pandas`: Data manipulation
- `python-dotenv`: Environment variable management

## Output

The scraper can save data in multiple formats:

- JSON files for structured data
- CSV files for tabular data
- Custom output formats via utility functions

## Best Practices

1. Always respect robots.txt and website terms of service
2. Use appropriate delays between requests
3. Handle errors gracefully
4. Monitor your scraping activity
5. Consider using proxies for large-scale scraping
6. Implement proper logging and monitoring

## License

This project is open source. Please use responsibly and in accordance with website terms of service.
