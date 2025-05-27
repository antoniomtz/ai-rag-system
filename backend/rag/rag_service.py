"""
RAG service that handles document retrieval and response generation with conversation history.
Supports website generation and streaming responses.
"""

from typing import List, Dict, Optional, AsyncGenerator
from together import Together
from .document_processor import DocumentProcessor
import logging
from langsmith import Client, traceable
import os
from langchain_together import ChatTogether
from langchain_core.messages import HumanMessage

# Configure logging
logger = logging.getLogger(__name__)

DEFAULT_LLM_MODEL="deepseek-ai/DeepSeek-V3"

# Initialize LangSmith client with better error handling
try:
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    if not langsmith_api_key:
        logger.warning("LANGSMITH_API_KEY not found in environment variables. LangSmith tracing will be disabled.")
        langsmith_client = None
    else:
        langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        langsmith_client = Client(
            api_key=langsmith_api_key,
            api_url=langsmith_endpoint
        )
        # Test the connection
        try:
            langsmith_client.list_projects()
            logger.info("Successfully connected to LangSmith")
        except Exception as e:
            logger.error(f"Failed to connect to LangSmith: {str(e)}")
            logger.warning("LangSmith tracing will be disabled")
            langsmith_client = None
except Exception as e:
    logger.error(f"Error initializing LangSmith client: {str(e)}")
    langsmith_client = None

class RAGService:
    """
    Service that combines document retrieval with response generation.
    Maintains only the last conversation for website updates.
    """
    
    def __init__(self):
        """
        Initialize the RAG service.
        """
        # Verify Together AI API key is set
        together_api_key = os.getenv("TOGETHER_API_KEY")
        if not together_api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is not set")
            
        self.document_processor = DocumentProcessor()  # This already handles document processing
        self.client = Together(api_key=together_api_key)
        self.last_query: Optional[str] = None
        self.last_response: Optional[str] = None
        
        # Log LangSmith status
        if langsmith_client is None:
            logger.warning("LangSmith tracing is disabled. Set valid LANGSMITH_API_KEY to enable tracing.")
        elif not os.getenv("LANGSMITH_TRACING", "").lower() == "true":
            logger.warning("LangSmith tracing is not enabled. Set LANGSMITH_TRACING=true to enable tracing.")

    def _format_context(self, search_results: List[Dict]) -> str:
        """Format search results into a context string."""
        context = "Here is the relevant context from the documents:\n\n"
        for doc, score in search_results:
            context += f"From {doc.metadata['source']} (relevance: {score:.2f}):\n"
            context += f"{doc.page_content}\n\n"
        return context

    def _format_conversation_history(self) -> str:
        """Format the last conversation into a string."""
        if not self.last_query or not self.last_response:
            return ""
            
        return f"""Previous conversation:
                User: {self.last_query}
                Assistant: {self.last_response}

                """

    def _update_history(self, query: str, response: str) -> None:
        """Update the last conversation."""
        self.last_query = query
        self.last_response = response
        logger.debug("Updated last conversation")

    def _get_website_prompt(self, query: str) -> List[Dict[str, str]]:
        """Generate a prompt for website creation using RAG context."""
        # Get relevant documents
        search_results = self.document_processor.similarity_search(query)
        context = self._format_context(search_results)
        history = self._format_conversation_history()
        
        return [
            {
                "role": "system",
                "content": """ONLY USE HTML, CSS AND JAVASCRIPT FOR YOUR RESPONSE, DO NOT INCLUDE ANY OTHER TEXT. 
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
                "content": f"""Here is the previous conversation (if any):

                {history}

                Here is the context with real data that should be used in the website:

                {context}

                Based on this context, previous conversation (if any), and the following request, create a website: {query}

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
                model=DEFAULT_LLM_MODEL,                
                temperature=0.7,
                max_tokens=8000,
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
        """Clear the last conversation."""
        self.last_query = None
        self.last_response = None
        logger.info("Last conversation cleared") 