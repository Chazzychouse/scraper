import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ScraperConfig:
    
    delay: float = field(default=1.0)
    timeout: int = field(default=10)
    user_agent: str = field(default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    max_requests_per_minute: int = field(default=60)
    
    output_dir: str = field(default="output")
    
    log_level: str = field(default="INFO")
    
    max_pages: int = field(default=50)
    max_depth: Optional[int] = field(default=None)
    stay_within_domain: bool = field(default=True)
    
    chunk_size: int = field(default=500)
    
    max_workers: int = field(default=3)
    
    def __post_init__(self):
        self._validate_config()
        self._normalize_config()
    
    @classmethod
    def from_env(cls) -> 'ScraperConfig':
        return cls(
            delay=float(os.getenv('SCRAPER_DELAY', '1.0')),
            timeout=int(os.getenv('SCRAPER_TIMEOUT', '10')),
            user_agent=os.getenv('SCRAPER_USER_AGENT', cls._get_default_user_agent()),
            max_requests_per_minute=int(os.getenv('SCRAPER_MAX_REQUESTS_PER_MINUTE', '60')),
            output_dir=os.getenv('SCRAPER_OUTPUT_DIR', 'output'),
            log_level=os.getenv('SCRAPER_LOG_LEVEL', 'INFO'),
            max_pages=int(os.getenv('SCRAPER_MAX_PAGES', '50')),
            max_depth=int(os.getenv('SCRAPER_MAX_DEPTH')) if os.getenv('SCRAPER_MAX_DEPTH') else None,
            stay_within_domain=os.getenv('SCRAPER_STAY_WITHIN_DOMAIN', 'true').lower() == 'true',
            chunk_size=int(os.getenv('SCRAPER_CHUNK_SIZE', '500')),
            max_workers=int(os.getenv('SCRAPER_MAX_WORKERS', '3'))
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ScraperConfig':
        return cls(**config_dict)
    
    @staticmethod
    def _get_default_user_agent() -> str:
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    
    def _validate_config(self):
        if self.delay < 0:
            raise ValueError("Delay must be non-negative")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_requests_per_minute <= 0:
            raise ValueError("Max requests per minute must be positive")
        if self.max_pages <= 0:
            raise ValueError("Max pages must be positive")
        if self.max_depth is not None and self.max_depth <= 0:
            raise ValueError("Max depth must be positive or None")
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.max_workers <= 0:
            raise ValueError("Max workers must be positive")
        
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Log level must be one of: {valid_log_levels}")
    
    def _normalize_config(self):
        self.log_level = self.log_level.upper()
        self.output_dir = str(Path(self.output_dir).resolve())
    
    def create_output_dir(self) -> None:
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def get_logging_config(self) -> Dict[str, Any]:
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
            },
            'handlers': {
                'default': {
                    'level': self.log_level,
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler',
                },
            },
            'loggers': {
                '': {
                    'handlers': ['default'],
                    'level': self.log_level,
                    'propagate': False
                }
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'delay': self.delay,
            'timeout': self.timeout,
            'user_agent': self.user_agent,
            'max_requests_per_minute': self.max_requests_per_minute,
            'output_dir': self.output_dir,
            'log_level': self.log_level,
            'max_pages': self.max_pages,
            'max_depth': self.max_depth,
            'stay_within_domain': self.stay_within_domain,
            'chunk_size': self.chunk_size,
            'max_workers': self.max_workers,
        }
    
    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
        
        self._validate_config()
        self._normalize_config()
    
    def __str__(self) -> str:
        return f"ScraperConfig(delay={self.delay}, timeout={self.timeout}, output_dir='{self.output_dir}')"


_config: Optional[ScraperConfig] = None


def get_config() -> ScraperConfig:
    global _config
    if _config is None:
        _config = ScraperConfig.from_env()
    return _config


def set_config(config: ScraperConfig) -> None:
    global _config
    _config = config


def reset_config() -> None:
    global _config
    _config = None


def create_output_dir():
    get_config().create_output_dir()