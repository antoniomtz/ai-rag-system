import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from .document_processor import DocumentProcessor, Document

class TestDocumentProcessor(unittest.TestCase):
    """Test cases for DocumentProcessor class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create temporary directories for test data and index
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.index_dir = Path(self.test_dir) / "faiss_index"
        self.data_dir.mkdir()
        self.index_dir.mkdir()

        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'TOGETHER_API_KEY': 'test_api_key'
        })
        self.env_patcher.start()

        # Initialize DocumentProcessor with test directories
        self.processor = DocumentProcessor(
            data_dir=str(self.data_dir),
            index_dir=str(self.index_dir),
            chunk_size=100,  # Smaller chunk size for testing
            chunk_overlap=10  # Smaller overlap for testing
        )

    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary directories
        shutil.rmtree(self.test_dir)
        # Stop environment variable patching
        self.env_patcher.stop()

    def test_initialization(self):
        """Test DocumentProcessor initialization."""
        self.assertEqual(self.processor.data_dir, self.data_dir)
        self.assertEqual(self.processor.index_dir, self.index_dir)
        self.assertIsNone(self.processor.vector_store)
        self.assertEqual(len(self.processor._query_embedding_cache), 0)

    @patch('langchain_community.vectorstores.FAISS')
    def test_process_documents_empty_directory(self, mock_faiss):
        """Test processing documents with empty directory."""
        with self.assertRaises(ValueError):
            self.processor.process_documents()

    @patch('pypdf.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        """Test PDF text extraction."""
        # Create a mock PDF file
        pdf_path = self.data_dir / "test.pdf"
        pdf_path.touch()

        # Mock PDF reader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test content"
        mock_pdf_reader.return_value.pages = [mock_page]

        text, metadata = self.processor._extract_text_from_pdf(pdf_path)
        
        self.assertEqual(text.strip(), "Test content")
        self.assertEqual(metadata["filename"], "test.pdf")
        self.assertEqual(metadata["pages"], 1)

    @patch('langchain_community.vectorstores.FAISS')
    def test_similarity_search_without_index(self, mock_faiss):
        """Test similarity search without initialized vector store."""
        with self.assertRaises(ValueError):
            self.processor.similarity_search("test query")

    def test_clear_query_cache(self):
        """Test clearing the query embedding cache."""
        # Add some test data to cache
        self.processor._query_embedding_cache["test"] = [0.1, 0.2, 0.3]
        self.processor.clear_query_cache()
        self.assertEqual(len(self.processor._query_embedding_cache), 0)

if __name__ == '__main__':
    unittest.main() 