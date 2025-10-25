import pytest
import os
import tempfile
from pathlib import Path

from scraper.config import ScraperConfig, get_config, set_config, reset_config

class TestScraperConfig:
    
    def test_default_config(self):
        config = ScraperConfig()
        
        assert config.delay == 1.0
        assert config.timeout == 10
        assert config.max_requests_per_minute == 60
        assert config.output_dir == "output"
        assert config.log_level == "INFO"
        assert config.max_pages == 50
        assert config.max_depth is None
        assert config.stay_within_domain is True
        assert config.chunk_size == 500
        assert config.max_workers == 3
        assert "Mozilla" in config.user_agent
    
    def test_config_validation(self):
        with pytest.raises(ValueError, match="Delay must be non-negative"):
            ScraperConfig(delay=-1.0)
        
        with pytest.raises(ValueError, match="Timeout must be positive"):
            ScraperConfig(timeout=0)
        
        with pytest.raises(ValueError, match="Max requests per minute must be positive"):
            ScraperConfig(max_requests_per_minute=-1)
        
        with pytest.raises(ValueError, match="Max pages must be positive"):
            ScraperConfig(max_pages=0)
        
        with pytest.raises(ValueError, match="Max depth must be positive or None"):
            ScraperConfig(max_depth=0)
        
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            ScraperConfig(chunk_size=-1)
        
        with pytest.raises(ValueError, match="Max workers must be positive"):
            ScraperConfig(max_workers=0)
        
        with pytest.raises(ValueError, match="Log level must be one of"):
            ScraperConfig(log_level="INVALID")
    
    def test_config_normalization(self):
        config = ScraperConfig(log_level="info", output_dir="./test_output")
        
        assert config.log_level == "INFO"
        assert str(config.output_dir).endswith("test_output")
    
    def test_from_dict(self):
        config_dict = {
            'delay': 2.0,
            'timeout': 15,
            'max_pages': 100,
            'chunk_size': 1000
        }
        
        config = ScraperConfig.from_dict(config_dict)
        
        assert config.delay == 2.0
        assert config.timeout == 15
        assert config.max_pages == 100
        assert config.chunk_size == 1000
        assert config.log_level == "INFO"
        assert config.max_workers == 3
    
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv('SCRAPER_DELAY', '2.5')
        monkeypatch.setenv('SCRAPER_TIMEOUT', '20')
        monkeypatch.setenv('SCRAPER_LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('SCRAPER_MAX_PAGES', '75')
        monkeypatch.setenv('SCRAPER_CHUNK_SIZE', '750')
        
        config = ScraperConfig.from_env()
        
        assert config.delay == 2.5
        assert config.timeout == 20
        assert config.log_level == "DEBUG"
        assert config.max_pages == 75
        assert config.chunk_size == 750
    
    def test_update_config(self):
        config = ScraperConfig()
        
        config.update(delay=3.0, timeout=25, max_pages=200)
        
        assert config.delay == 3.0
        assert config.timeout == 25
        assert config.max_pages == 200
        assert config.log_level == "INFO"
        assert config.chunk_size == 500
    
    def test_update_invalid_key(self):
        config = ScraperConfig()
        
        with pytest.raises(ValueError, match="Unknown configuration key"):
            config.update(invalid_key="value")
    
    def test_to_dict(self):
        config = ScraperConfig(delay=2.0, timeout=15, max_pages=100)
        config_dict = config.to_dict()
        
        assert config_dict['delay'] == 2.0
        assert config_dict['timeout'] == 15
        assert config_dict['max_pages'] == 100
        assert config_dict['log_level'] == "INFO"
        assert 'user_agent' in config_dict
    
    def test_create_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ScraperConfig(output_dir=os.path.join(temp_dir, "test_output"))
            
            assert not os.path.exists(config.output_dir)
            
            config.create_output_dir()
            
            assert os.path.exists(config.output_dir)
            assert os.path.isdir(config.output_dir)
    
    def test_get_logging_config(self):
        config = ScraperConfig(log_level="DEBUG")
        logging_config = config.get_logging_config()
        
        assert logging_config['version'] == 1
        assert logging_config['loggers']['']['level'] == "DEBUG"
        assert 'formatters' in logging_config
        assert 'handlers' in logging_config

class TestGlobalConfig:
    
    def test_get_config_default(self):
        reset_config()
        config = get_config()
        
        assert isinstance(config, ScraperConfig)
        assert config.delay == 1.0
        assert config.timeout == 10
    
    def test_set_config(self):
        custom_config = ScraperConfig(delay=5.0, timeout=30)
        set_config(custom_config)
        
        retrieved_config = get_config()
        assert retrieved_config is custom_config
        assert retrieved_config.delay == 5.0
        assert retrieved_config.timeout == 30
    
    def test_reset_config(self):
        custom_config = ScraperConfig(delay=5.0)
        set_config(custom_config)
        
        reset_config()
        
        config = get_config()
        assert config.delay == 1.0  # Default value
        assert config is not custom_config  # Different instance

class TestConfigIntegration:
    
    def test_scraper_with_config(self):
        from scraper.core.scraper import WebScraper
        
        custom_config = ScraperConfig(delay=2.0, timeout=15)
        scraper = WebScraper(config=custom_config)
        
        assert scraper.delay == 2.0
        assert scraper.timeout == 15
        assert scraper.config is custom_config
        
        scraper.close()
    
    def test_scraper_with_parameter_override(self):
        from scraper.core.scraper import WebScraper
        
        custom_config = ScraperConfig(delay=2.0, timeout=15)
        scraper = WebScraper(delay=3.0, config=custom_config)
        
        assert scraper.delay == 3.0
        assert scraper.timeout == 15
        
        scraper.close()
    
    def test_api_with_config(self):
        from scraper.api.scraper_api import ScraperAPI
        
        custom_config = ScraperConfig(delay=2.0, timeout=15, max_pages=100)
        api = ScraperAPI(config=custom_config)
        
        assert api.delay == 2.0
        assert api.timeout == 15
        assert api.config is custom_config
        
        api.close()
