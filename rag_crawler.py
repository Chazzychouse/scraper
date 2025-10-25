#!/usr/bin/env python3
"""
Quick RAG crawler implementation.
Crawls a website using RAG API with max_pages=500 and max_depth=2,
then saves the results to a JSON file.
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scraper"))

try:
    from scraper.api.rag_scraper import RAGScraper
    from scraper.config import ScraperConfig
except ImportError as e:
    print(f"Error importing scraper modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def crawl_and_save(url: str, output_file: str = None):
    """
    Crawl a website using RAG scraper and save results to file.
    
    Args:
        url: The starting URL to crawl
        output_file: Output file path (defaults to timestamped filename)
    """
    print(f"Starting RAG crawl of: {url}")
    print("Parameters: max_pages=500, max_depth=2")
    
    try:
        # Initialize config and RAG scraper
        config = ScraperConfig()
        rag_scraper = RAGScraper(config=config)
        
        # Perform the crawl
        print("Crawling in progress...")
        results = rag_scraper.crawl_for_rag(
            start_url=url,
            max_pages=500,
            max_depth=2,
            stay_within_domain=True
        )
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            output_file = f"rag_crawl_{domain}_{timestamp}.json"
        
        output_data = {
            "crawl_info": {
                "start_url": url,
                "max_pages": 500,
                "max_depth": 2,
                "stay_within_domain": True,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_urls_visited": len(results.get("urls", [])),
                "total_chunks_extracted": len(results.get("data", []))
            },
            "results": results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nCrawl completed successfully!")
        print(f"Results saved to: {output_file}")
        print(f"URLs visited: {len(results.get('urls', []))}")
        print(f"Chunks extracted: {len(results.get('data', []))}")
        
        if results.get("data"):
            print(f"\nSample chunks (first 3):")
            for i, chunk in enumerate(results["data"][:3]):
                print(f"\nChunk {i+1}:")
                print(f"  Title: {chunk.get('title', 'N/A')}")
                print(f"  URL: {chunk.get('url', 'N/A')}")
                print(f"  Text preview: {chunk.get('text', '')[:100]}...")
        
        rag_scraper.close()
        
    except Exception as e:
        print(f"Error during crawl: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="RAG Website Crawler")
    parser.add_argument("url", help="Starting URL to crawl")
    parser.add_argument("-o", "--output", help="Output file path (optional)")
    
    args = parser.parse_args()
    
    if not args.url.startswith(("http://", "https://")):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)
    
    crawl_and_save(args.url, args.output)


if __name__ == "__main__":
    main()
