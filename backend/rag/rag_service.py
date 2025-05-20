"""
RAG service that handles document retrieval and response generation with conversation history.
Supports website generation and streaming responses.
"""

from typing import List, Dict, Optional, AsyncGenerator, Generator
from together import Together
from .document_processor import DocumentProcessor
import logging
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class RAGService:
    """
    Service that combines document retrieval with conversation history for context-aware responses.
    
    This class:
    1. Maintains conversation history
    2. Retrieves relevant documents for each query
    3. Generates responses using both conversation context and retrieved documents
    4. Supports website generation and streaming responses
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

    def _get_website_prompt(self, query: str) -> List[Dict[str, str]]:
        """Generate a prompt for website creation using RAG context."""
        # Get relevant documents
        search_results = self.document_processor.similarity_search(query)
        context = self._format_context(search_results)
        
        return [
            {
                "role": "system",
                "content": """ONLY USE HTML, CSS AND JAVASCRIPT. 
                - Use TailwindCSS for styling (import <script src='https://cdn.tailwindcss.com'></script> in the head).
                - For icons, use open source libraries like Font Awesome (import <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'> in the head) or Heroicons.
                - For fonts, use Google Fonts (import the font in the head).
                - For animations, you can use Animate.css (import <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css'>).
                - You can use open source illustrations from unDraw or SVGBackgrounds.
                - Be creative: use cards, gradients, shadows, hover effects, and modern layouts.
                - Make the UI visually appealing and unique, not just plain layouts.
                - ALWAYS GIVE THE RESPONSE AS A SINGLE HTML FILE.
                - Use the provided context data for content, but make the design stand out.
                
                IMPORTANT: Use the provided context to generate the website content. The context contains real data that should be used
                in the website. For example, if the context contains product information, use those actual products, prices, and details
                in the website. Do not make up or use generic data."""
            },
            {
                "role": "user",
                "content": f"""Here is the context with real data that should be used in the website:

                {context}

                Based on this context and the following request, create a website: {query}

                Remember to use the actual data from the context in the website."""
            }
        ]

    async def get_response_stream(self, query: str) -> AsyncGenerator[str, None]:
        """
        Get a streaming response using RAG with conversation history.
        
        Args:
            query: The user's query
            
        Yields:
            Chunks of the generated response
            
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
            
            # Get streaming response from Together AI
            stream = self.client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            accumulated_response = ""
            
            # Convert synchronous generator to async generator
            while True:
                try:
                    chunk = next(stream)
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        accumulated_response += content
                        yield content
                except StopIteration:
                    break
                await asyncio.sleep(0)  # Allow other tasks to run
            
            # Update conversation history
            self._update_history(query, accumulated_response)

        except Exception as e:
            error_msg = f"Error getting streaming RAG response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"I encountered an error while processing your request: {str(e)}"

    async def get_website_response_stream(self, query: str) -> AsyncGenerator[str, None]:
        """
        Get a streaming response for website generation using RAG context.
        
        Args:
            query: The user's website request
            
        Yields:
            Chunks of the generated website code
            
        Raises:
            Exception: If there's an error processing the request
        """
        try:
            messages = self._get_website_prompt(query)
            
            # Get streaming response from Together AI
            stream = self.client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
                stream=True
            )
            
            accumulated_response = ""
            
            # Convert synchronous generator to async generator
            while True:
                try:
                    chunk = next(stream)
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        accumulated_response += content
                        yield content
                except StopIteration:
                    break
                await asyncio.sleep(0)  # Allow other tasks to run
            
            # Update conversation history
            self._update_history(query, accumulated_response)

        except Exception as e:
            error_msg = f"Error getting streaming website response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"I encountered an error while generating the website: {str(e)}"

    def get_response(self, query: str) -> str:
        """
        Get a non-streaming response using RAG with conversation history.
        
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

    def get_website_response(self, query: str) -> str:
        """
        Get a non-streaming response for website generation using RAG context.
        
        Args:
            query: The user's website request
            
        Returns:
            The generated website code
            
        Raises:
            Exception: If there's an error processing the request
        """
        try:
            messages = self._get_website_prompt(query)
            
            # Get response from Together AI
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
            )
            
            response_text = response.choices[0].message.content
            
            # Update conversation history
            self._update_history(query, response_text)
            
            return response_text

        except Exception as e:
            error_msg = f"Error getting website response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"I encountered an error while generating the website: {str(e)}"

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared") 