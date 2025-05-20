"""
RAG service that handles document retrieval and response generation with conversation history.
Supports website generation and streaming responses.
"""

from typing import List, Dict, Optional, AsyncGenerator, Generator
from together import Together
from .document_processor import DocumentProcessor
import logging
import asyncio
from langsmith import Client, traceable
import os
from langchain_together import ChatTogether
from langchain_core.messages import HumanMessage

# Configure logging
logger = logging.getLogger(__name__)

# Initialize LangSmith client
langsmith_client = Client(
    api_key=os.getenv("LANGSMITH_API_KEY"),
    api_url=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
)

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
        
        # Verify LangSmith tracing is enabled
        if not os.getenv("LANGSMITH_TRACING", "").lower() == "true":
            logger.warning("LangSmith tracing is not enabled. Set LANGSMITH_TRACING=true to enable tracing.")

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
        history = self._format_conversation_history()
        
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
                "content": f"""Here is the conversation history so far:

                {history}

                Here is the context with real data that should be used in the website:

                {context}

                Based on this context, conversation history, and the following request, create a website: {query}

                Remember to use the actual data from the context in the website and maintain consistency with previous interactions."""
            }
        ]

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
            llm = ChatTogether(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",                
                temperature=0.7,
                max_tokens=4000,
                streaming=True
            )

            response = ""
            for chunk in llm.stream(messages):
                if chunk.content:
                    response += chunk.content
                    yield chunk.content
            
            # Update conversation history
            self._update_history(query, response)

        except Exception as e:
            error_msg = f"Error getting streaming website response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"I encountered an error while generating the website: {str(e)}"

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared") 