# Run all tests
pytest

# Run with coverage
pytest --cov=scraper --cov-report=html

# Run specific test file
pytest tests/test_scraper.py

# Run specific test class or function
pytest tests/test_scraper.py::TestGetPage::test_get_page_success

# Run tests matching a pattern
pytest -k "test_extract"

# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s
