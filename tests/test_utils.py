
import pytest
import json
from pathlib import Path
from scraper.utils import save_to_json, save_to_csv, clean_text, is_valid_url

class TestSaveToJson:
    
    def test_save_to_json(self, tmp_path):
        data = [{"name": "test", "value": 123}]
        
        save_to_json(data, "test", output_dir=str(tmp_path))
        
        filepath = tmp_path / "test.json"
        assert filepath.exists()
        
        with open(filepath, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == data

class TestSaveToCsv:
    
    def test_save_to_csv(self, tmp_path):
        data = [{"name": "test", "value": 123}]
        
        save_to_csv(data, "test", output_dir=str(tmp_path))
        
        filepath = tmp_path / "test.csv"
        assert filepath.exists()
    
    def test_save_empty_csv(self, tmp_path, capsys):
        save_to_csv([], "test", output_dir=str(tmp_path))
        
        captured = capsys.readouterr()
        assert "No data to save" in captured.out

class TestCleanText:

    def test_clean_text_basic(self):
        text = "  Hello   World  "
        assert clean_text(text) == "Hello World"
    
    def test_clean_text_with_newlines(self):
        text = "Hello\nWorld\r\nTest"
        assert clean_text(text) == "Hello World Test"
    
    def test_clean_text_empty(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""

class TestIsValidUrl:

    @pytest.mark.parametrize("url", [
        "https://example.com",
        "http://test.org/path",
        "https://example.com:8080/page?param=value"
    ])
    def test_valid_urls(self, url):
        assert is_valid_url(url) is True
    
    @pytest.mark.parametrize("url", [
        "not a url",
        "example.com",
        "/relative/path",
        ""
    ])
    def test_invalid_urls(self, url):
        assert is_valid_url(url) is False