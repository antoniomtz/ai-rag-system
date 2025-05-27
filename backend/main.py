"""
FastAPI backend for the AI chat application.
Handles chat requests and integrates with Together AI for generating responses.
Supports streaming responses and website generation.
"""

import logging
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from rag.rag_service import RAGService

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
logger.info(f"Looking for .env file at: {env_path}")
load_dotenv(dotenv_path=env_path)

# Debug log environment variables (without exposing full values)
logger.info("Environment variables loaded:")
logger.info(f"TOGETHER_API_KEY present: {'Yes' if os.getenv('TOGETHER_API_KEY') else 'No'}")
logger.info(f"LANGSMITH_API_KEY present: {'Yes' if os.getenv('LANGSMITH_API_KEY') else 'No'}")
logger.info(f"LANGSMITH_ENDPOINT: {os.getenv('LANGSMITH_ENDPOINT', 'Not set')}")
logger.info(f"LANGSMITH_TRACING: {os.getenv('LANGSMITH_TRACING', 'Not set')}")

# Verify required environment variables
required_env_vars = ['TOGETHER_API_KEY', 'LANGSMITH_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG service
try:
    rag_service = RAGService()
    logger.info("RAG service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG service: {str(e)}")
    raise

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = False

async def generate_stream(response_generator):
    """
    Generate a stream of responses from the AI.
    Each response is formatted as a Server-Sent Event.
    """
    try:
        async for chunk in response_generator:
            # Format as SSE
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        # Send done signal
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Error in stream generation: {str(e)}", exc_info=True)
        error_msg = json.dumps({"error": str(e)})
        yield f"data: {error_msg}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Handle chat requests and generate AI responses.
    Supports both streaming and non-streaming responses.
    """
    try:
        # Get the last user message
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        last_user_message = user_messages[-1].content
        logger.info(f"Received chat request with message: {last_user_message}")

        if request.stream:
            # For streaming responses, use website generation for all requests
            response_generator = rag_service.get_website_response_stream(last_user_message)
            return StreamingResponse(
                generate_stream(response_generator),
                media_type="text/event-stream"
            )
        else:
            # For non-streaming responses, use website generation for all requests
            response = rag_service.get_website_response(last_user_message)
            return {"role": "assistant", "content": response}

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        if request.stream:
            return StreamingResponse(
                generate_stream([f"Error: {str(e)}"]),
                media_type="text/event-stream"
            )
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/clear")
async def clear_chat():
    """Clear the chat context and history."""
    try:
        rag_service.clear_history()
        return {"status": "success", "message": "Chat context cleared"}
    except Exception as e:
        logger.error(f"Error clearing chat context: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)