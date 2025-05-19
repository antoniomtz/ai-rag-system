"""
RAG service that handles document retrieval and response generation with conversation history.
"""

from typing import List, Dict, Optional
from together import Together
from .document_processor import DocumentProcessor
import logging

# Configure logging
logger = logging.getLogger(__name__)

class RAGService:
    """
    Service that combines document retrieval with conversation history for context-aware responses.
    
    This class:
    1. Maintains conversation history
    2. Retrieves relevant documents for each query
    3. Generates responses using both conversation context and retrieved documents
    """
    
    def __init__(self, max_history: int = 5):
        """
        Initialize the RAG service.
        
        Args:
            max_history: Maximum number of conversation turns to keep in history
        """
        self.document_processor = DocumentProcessor()
        self.client = Together()
        self.max_history = max_history
        self.conversation_history: List[Dict[str, str]] = []
        self._initialize_rag()

    def _initialize_rag(self) -> None:
        """Initialize the RAG system by processing documents."""
        try:
            self.document_processor.process_documents()
        except Exception as e:
            logger.error(f"Error initializing RAG system: {str(e)}", exc_info=True)
            raise

    def _format_context(self, search_results: List[Dict]) -> str:
        """Format search results into a context string."""
        context = "Here is the relevant context from the documents:\n\n"
        for doc, score in search_results:
            context += f"From {doc.metadata['source']} (relevance: {score:.2f}):\n"
            context += f"{doc.page_content}\n\n"
        return context

    def _format_conversation_history(self) -> str:
        """Format conversation history into a string."""
        if not self.conversation_history:
            return ""
            
        history = "Previous conversation:\n"
        for turn in self.conversation_history[-self.max_history:]:
            history += f"User: {turn['user']}\n"
            history += f"Assistant: {turn['assistant']}\n\n"
        return history

    def _update_history(self, query: str, response: str) -> None:
        """Update conversation history with new turn."""
        self.conversation_history.append({
            "user": query,
            "assistant": response
        })
        # Keep only the last max_history turns
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def get_response(self, query: str) -> str:
        """
        Get a response using RAG with conversation history.
        
        Args:
            query: The user's query
            
        Returns:
            The generated response
            
        Raises:
            Exception: If there's an error processing the request
        """
        try:
            # Get relevant documents
            search_results = self.document_processor.similarity_search(query)
            
            # Format context and history
            context = self._format_context(search_results)
            history = self._format_conversation_history()
            
            # Create prompt with context and history
            prompt = f"""You are a helpful assistant that answers questions based on the provided context and conversation history.
            Use the following context and conversation history to answer the question.
            If the context doesn't contain relevant information, say so.
            Maintain consistency with previous responses and use the conversation history to understand context.

            {history}
            {context}

            Current Question: {query}

            Answer:"""
            
            # Get response from Together AI
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000,
            )
            
            response_text = response.choices[0].message.content
            
            # Update conversation history
            self._update_history(query, response_text)
            
            return response_text

        except Exception as e:
            error_msg = f"Error getting RAG response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"I encountered an error while processing your request: {str(e)}"

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared") 