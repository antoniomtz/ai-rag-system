"""
Document processor for RAG system that handles PDF document loading, chunking, and vector storage.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_together import TogetherEmbeddings
from langchain.schema import Document
from langsmith import traceable

# Configure logging
logger = logging.getLogger(__name__)

# Constants for configuration
DEFAULT_CHUNK_SIZE = 4000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_SEPARATORS = ["\n\n", "\n", ".", "!", "?", ",", " ", ""]
DEFAULT_EMBEDDING_MODEL = "togethercomputer/m2-bert-80M-8k-retrieval"
DEFAULT_DATA_DIR = "data"
DEFAULT_INDEX_DIR = "faiss_index"
DEFAULT_SIMILARITY_SEARCH_K = 1

class DocumentProcessor:
    """
    Handles document processing, chunking, and vector storage for RAG system.
    
    This class manages the entire document processing pipeline:
    1. Loading PDF documents from a directory
    2. Splitting documents into chunks
    3. Creating and managing vector embeddings
    4. Storing and retrieving vectors using FAISS
    """
    
    def __init__(
        self,
        data_dir: str = DEFAULT_DATA_DIR,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        index_dir: str = DEFAULT_INDEX_DIR,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: List[str] = DEFAULT_SEPARATORS
    ) -> None:
        """
        Initialize the document processor.
        
        Args:
            data_dir: Directory containing PDF documents to process
            embedding_model: The Together AI model to use for embeddings
            index_dir: Directory where the FAISS index will be stored
            chunk_size: Size of text chunks for splitting documents
            chunk_overlap: Overlap between chunks
            separators: List of separators to use for text splitting
        """
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)
        
        # Initialize embeddings
        self.embeddings = TogetherEmbeddings(model=embedding_model)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=separators
        )
        
        # Initialize vector store
        self.vector_store: Optional[FAISS] = None
        
        # Load or create index
        self._load_or_create_index()

    def _load_or_create_index(self) -> None:
        """
        Load existing FAISS index or create a new one if it doesn't exist.
        
        Raises:
            Exception: If there's an error loading or creating the index
        """
        try:
            if self.index_dir.exists() and any(self.index_dir.iterdir()):
                logger.info(f"Loading existing FAISS index from {self.index_dir}")
                self.vector_store = FAISS.load_local(
                    folder_path=str(self.index_dir),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True  # Safe because we create these files ourselves
                )
                logger.info("Successfully loaded FAISS index")
            else:
                logger.info("No existing FAISS index found, processing documents...")
                self.process_documents()
        except Exception as e:
            logger.error(f"Error loading/creating index: {str(e)}", exc_info=True)
            raise

    def _save_index(self) -> None:
        """
        Save the FAISS index to disk.
        
        Raises:
            Exception: If there's an error saving the index
        """
        if not self.vector_store:
            logger.warning("No vector store to save")
            return

        try:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving FAISS index to {self.index_dir}")
            self.vector_store.save_local(folder_path=str(self.index_dir))
            logger.info("Successfully saved FAISS index")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}", exc_info=True)
            raise

    def _extract_text_from_pdf(self, pdf_file: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from a PDF file.
        
        Args:
            pdf_file: Path to the PDF file
            
        Returns:
            Tuple of (text content, metadata dictionary)
            
        Raises:
            Exception: If there's an error processing the PDF
        """
        try:
            reader = PdfReader(pdf_file)
            text = ""
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text += page.extract_text() + "\n"
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num} of {pdf_file}: {str(e)}")
            
            if not text.strip():
                logger.warning(f"No text extracted from {pdf_file}")
                return "", {}
                
            metadata = {
                "source": str(pdf_file),
                "pages": len(reader.pages),
                "filename": pdf_file.name
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}", exc_info=True)
            raise

    def load_documents(self) -> List[Document]:
        """
        Load all PDF documents from the data directory.
        
        Returns:
            List of Document objects containing content and metadata
            
        Raises:
            FileNotFoundError: If the data directory doesn't exist
            Exception: If there's an error processing any document
        """
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory {self.data_dir} does not exist")
        
        documents: List[Document] = []
        pdf_files = list(self.data_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {self.data_dir}")
            return documents
            
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing {pdf_file}")
                text, metadata = self._extract_text_from_pdf(pdf_file)
                if text and metadata:
                    documents.append(Document(page_content=text, metadata=metadata))
                    logger.info(f"Successfully processed {pdf_file}")
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}", exc_info=True)
                raise
        
        return documents

    def process_documents(self) -> None:
        """
        Process documents and create vector store.
        
        This method:
        1. Loads documents from the data directory
        2. Splits them into chunks
        3. Creates embeddings
        4. Builds and saves the FAISS index
        
        Raises:
            ValueError: If no documents are found to process
            Exception: If there's an error creating the vector store
        """
        try:
            documents = self.load_documents()
            if not documents:
                raise ValueError("No documents found to process")

            logger.info("Splitting documents into chunks...")
            # Split documents into chunks
            texts: List[str] = []
            metadatas: List[Dict[str, Any]] = []
            
            for doc in documents:
                chunks = self.text_splitter.split_text(doc.page_content)
                texts.extend(chunks)
                metadatas.extend([doc.metadata] * len(chunks))
            
            logger.info(f"Created {len(texts)} chunks from {len(documents)} documents")

            # Create vector store
            logger.info("Creating vector store...")
            self.vector_store = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            logger.info("Vector store created successfully")
            
            # Save the index
            self._save_index()
            
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}", exc_info=True)
            raise

    @traceable
    def similarity_search(
        self,
        query: str,
        k: int = DEFAULT_SIMILARITY_SEARCH_K
    ) -> List[Tuple[Document, float]]:
        """
        Perform similarity search on the vector store.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
            
        Raises:
            ValueError: If vector store is not initialized
            Exception: If there's an error performing the search
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call process_documents first.")
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.debug(f"Found {len(results)} results for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}", exc_info=True)
            raise 