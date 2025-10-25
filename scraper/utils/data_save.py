import json
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path


def save_to_json(data: List[Dict[str, Any]], filename: str, output_dir: str = "output"):
    Path(output_dir).mkdir(exist_ok=True)
    filepath = Path(output_dir) / f"{filename}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to {filepath}")


def save_to_csv(data: List[Dict[str, Any]], filename: str, output_dir: str = "output"):
    Path(output_dir).mkdir(exist_ok=True)
    filepath = Path(output_dir) / f"{filename}.csv"
    
    if data:
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"Data saved to {filepath}")
    else:
        print("No data to save")


def clean_text(text: str) -> str:
    if not text:
        return ""
    
    text = ' '.join(text.split())
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    return text.strip()


def is_valid_url(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
