import pytest
from bs4 import BeautifulSoup
from scraper.extractors.basic import BasicExtractor
from scraper.extractors.rag import RAGExtractor


class TestBasicExtractor:
    
    @pytest.fixture
    def extractor(self):
        return BasicExtractor()
    
    @pytest.fixture
    def sample_html(self):
        return """
        <html>
            <head>
                <title>Test Page Title</title>
            </head>
            <body>
                <h1>Main Heading</h1>
                <p>This is some content with multiple words and sentences.</p>
                <a href="/link1">Link 1</a>
                <a href="/link2">Link 2</a>
                <a href="https://external.com">External Link</a>
                <div class="content">
                    <p>More content here</p>
                </div>
            </body>
        </html>
        """
    
    def test_extract_basic_metadata(self, extractor, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        metadata = {'depth': 2, 'url': 'https://example.com/test'}
        
        result = extractor.extract('https://example.com/test', soup, metadata)
        
        assert isinstance(result, dict)
        assert result['url'] == 'https://example.com/test'
        assert result['depth'] == 2
        assert result['title'] == 'Test Page Title'
        assert result['text_length'] > 0
        assert result['link_count'] == 3  # 3 <a> tags
    
    def test_extract_no_title(self, extractor):
        html = "<html><body><p>Content without title</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com'}
        
        result = extractor.extract('https://example.com', soup, metadata)
        
        assert result['title'] == ''
        assert result['text_length'] > 0
        assert result['link_count'] == 0
    
    def test_extract_empty_html(self, extractor):
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com'}
        
        result = extractor.extract('https://example.com', soup, metadata)
        
        assert result['url'] == 'https://example.com'
        assert result['depth'] == 0
        assert result['title'] == ''
        assert result['text_length'] == 0
        assert result['link_count'] == 0
    
    def test_extract_with_metadata(self, extractor, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        metadata = {
            'depth': 5,
            'url': 'https://example.com/deep/page',
            'custom_field': 'custom_value'
        }
        
        result = extractor.extract('https://example.com/deep/page', soup, metadata)
        
        assert result['url'] == 'https://example.com/deep/page'
        assert result['depth'] == 5
        # Custom metadata should not be included in result
        assert 'custom_field' not in result


class TestRAGExtractor:
    
    @pytest.fixture
    def extractor(self):
        return RAGExtractor(chunk_size_target=200)
    
    @pytest.fixture
    def sample_html_with_structure(self):
        return """
        <html>
            <head><title>Documentation Page</title></head>
            <body>
                <main>
                    <h1>Main Topic</h1>
                    <h2>Section 1</h2>
                    <p>This is the first section with some content that explains the main concept.</p>
                    <p>This is additional content in the same section.</p>
                    
                    <h2>Section 2</h2>
                    <p>This is the second section with different content.</p>
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
    
    def test_extract_returns_list(self, extractor, sample_html_with_structure):
        soup = BeautifulSoup(sample_html_with_structure, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/docs'}
        
        result = extractor.extract('https://example.com/docs', soup, metadata)
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_extract_chunk_structure(self, extractor, sample_html_with_structure):
        soup = BeautifulSoup(sample_html_with_structure, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/docs'}
        
        chunks = extractor.extract('https://example.com/docs', soup, metadata)
        
        assert len(chunks) >= 1
        
        first_chunk = chunks[0]
        required_fields = ['text', 'title', 'page_title', 'h1', 'h2', 'h3', 'url', 'source', 'depth', 'char_count', 'chunk_id']
        
        for field in required_fields:
            assert field in first_chunk
        
        assert first_chunk['url'] == 'https://example.com/docs'
        assert first_chunk['source'] == 'https://example.com/docs'
        assert first_chunk['depth'] == 0
        assert first_chunk['page_title'] == 'Documentation Page'
        assert first_chunk['h1'] == 'Main Topic'
        assert first_chunk['char_count'] > 0
        assert len(first_chunk['text']) > 0
    
    def test_extract_multiple_sections(self, extractor, sample_html_with_structure):
        soup = BeautifulSoup(sample_html_with_structure, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/docs'}
        
        chunks = extractor.extract('https://example.com/docs', soup, metadata)
        
        assert len(chunks) >= 2
        
        h2_values = [chunk.get('h2', '') for chunk in chunks if chunk.get('h2')]
        assert len(set(h2_values)) > 1
    
    def test_extract_code_blocks(self, extractor, sample_html_with_structure):
        soup = BeautifulSoup(sample_html_with_structure, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/docs'}
        
        chunks = extractor.extract('https://example.com/docs', soup, metadata)
        
        code_chunk = None
        for chunk in chunks:
            if '[CODE]' in chunk['text']:
                code_chunk = chunk
                break
        
        assert code_chunk is not None
        assert '[CODE]' in code_chunk['text']
        assert 'def example_function():' in code_chunk['text']
        assert '[/CODE]' in code_chunk['text']
    
    def test_extract_hierarchical_titles(self, extractor, sample_html_with_structure):
        soup = BeautifulSoup(sample_html_with_structure, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/docs'}
        
        chunks = extractor.extract('https://example.com/docs', soup, metadata)
        
        for chunk in chunks:
            if chunk.get('h2') and chunk.get('h3'):
                assert ' > ' in chunk['title']
                assert chunk['h2'] in chunk['title']
                assert chunk['h3'] in chunk['title']
    
    def test_extract_chunk_size_target(self, extractor):
        long_content = "This is a very long piece of content. " * 50  # ~2000 characters
        html = f"""
        <html>
            <head><title>Long Content Page</title></head>
            <body>
                <main>
                    <h1>Main Topic</h1>
                    <h2>Section 1</h2>
                    <p>{long_content}</p>
                    <h2>Section 2</h2>
                    <p>{long_content}</p>
                </main>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/long'}
        
        chunks = extractor.extract('https://example.com/long', soup, metadata)
        
        assert len(chunks) > 1
        
        for chunk in chunks:
            char_count = chunk.get('char_count', 0)
            assert char_count <= extractor.chunk_size_target * 10
    
    def test_extract_empty_content(self, extractor):
        html = "<html><body><main></main></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/empty'}
        
        chunks = extractor.extract('https://example.com/empty', soup, metadata)
        
        assert chunks == []
    
    def test_extract_no_main_content(self, extractor):
        html = """
        <html>
            <head><title>No Main Content</title></head>
            <body>
                <h1>Title</h1>
                <p>Content without main tag</p>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/no-main'}
        
        chunks = extractor.extract('https://example.com/no-main', soup, metadata)
        
        assert len(chunks) > 0
        assert chunks[0]['text'] != ''
    
    def test_extract_chunk_id_generation(self, extractor, sample_html_with_structure):
        soup = BeautifulSoup(sample_html_with_structure, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/docs'}
        
        chunks = extractor.extract('https://example.com/docs', soup, metadata)
        
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id', '')
            assert chunk_id != ''
            assert 'https://example.com/docs' in chunk_id
            
            if chunk.get('h1'):
                assert chunk['h1'] in chunk_id
            if chunk.get('h2'):
                assert chunk['h2'] in chunk_id
    
    def test_extract_with_metadata(self, extractor, sample_html_with_structure):
        soup = BeautifulSoup(sample_html_with_structure, 'html.parser')
        metadata = {
            'depth': 3,
            'url': 'https://example.com/deep/page',
            'custom_field': 'custom_value'
        }
        
        chunks = extractor.extract('https://example.com/deep/page', soup, metadata)
        
        for chunk in chunks:
            assert chunk['url'] == 'https://example.com/deep/page'
            assert chunk['source'] == 'https://example.com/deep/page'
            assert chunk['depth'] == 3
            # Custom metadata should not be included
            assert 'custom_field' not in chunk
    
    def test_extract_different_chunk_sizes(self):
        small_extractor = RAGExtractor(chunk_size_target=50)
        large_extractor = RAGExtractor(chunk_size_target=1000)
        
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <main>
                    <h1>Main Topic</h1>
                    <h2>Section 1</h2>
                    <p>This is a section with some content that should be chunked differently based on the target size.</p>
                    <h2>Section 2</h2>
                    <p>Another section with more content to test chunking behavior.</p>
                </main>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {'depth': 0, 'url': 'https://example.com/test'}
        
        small_chunks = small_extractor.extract('https://example.com/test', soup, metadata)
        large_chunks = large_extractor.extract('https://example.com/test', soup, metadata)
        
        assert len(small_chunks) >= len(large_chunks)
        
        for chunk in small_chunks:
            assert chunk['char_count'] <= small_extractor.chunk_size_target * 2
        
        for chunk in large_chunks:
            assert chunk['char_count'] <= large_extractor.chunk_size_target * 2
