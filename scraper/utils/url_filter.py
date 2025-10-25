from urllib.parse import urlparse


class URLFilter:
    
    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url)
        normalized = parsed._replace(fragment='').geturl()
        if normalized.endswith('/') and parsed.path != '/':
            normalized = normalized.rstrip('/')
        return normalized
    
    @staticmethod
    def get_domain(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https']
    
    @staticmethod
    def same_domain(url1: str, url2: str) -> bool:
        if not url2.startswith(('http://', 'https://')):
            domain1 = URLFilter.get_domain(url1)
            return domain1.endswith(url2) or domain1 == f"https://{url2}" or domain1 == f"http://{url2}"
        
        return URLFilter.get_domain(url1) == URLFilter.get_domain(url2)
