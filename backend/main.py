"""
FastAPI backend for the AI chat application.
Handles chat requests and integrates with Together AI for generating responses.
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from together import Together

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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

# Initialize Together AI client
together_client = Together()

@app.post("/api/chat")
async def chat(request: dict):
    """
    Handle chat requests and generate AI responses.
    Expects a request body with a 'messages' list containing 'role' and 'content' for each message.
    """
    try:
        messages = request.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        # Get the last user message
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content")
                break

        if not last_user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # Format the prompt for the AI
        prompt = f"Human: {last_user_message}\n\nAssistant:"
        
        # Generate AI response
        response = together_client.complete.create(
            prompt=prompt,
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            max_tokens=1000,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1.1,
            stop=["Human:", "Assistant:"]
        )
        
        # Extract and return the response
        return {
            "role": "assistant",
            "content": response["output"]["choices"][0]["text"].strip()
        }
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 