# AI Website Builder with RAG

An intelligent system that generates static websites using Retrieval-Augmented Generation (RAG) and natural language processing. The system leverages document context and user instructions to create beautiful, responsive websites through an intuitive chat interface.

## Project Overview

This project combines the power of RAG with modern web technologies to create an AI-powered website builder. Users can provide documents (PDFs) containing content and styling preferences, and then use natural language to instruct the AI to generate websites that incorporate this content.

## Demo (youtube)

[![AI website builder](https://img.youtube.com/vi/gEMA2NlowpY/0.jpg)](https://www.youtube.com/watch?v=gEMA2NlowpY)

### Key Features

- Document-based context retrieval using RAG
- Natural language to website generation
- Interactive chat interface
- Live website preview
- Responsive and modern UI design

## System Architecture

### Core Components

#### Backend (Python/FastAPI)
- **RAG System**: Document processing and context retrieval
  - PDF document ingestion and chunking
  - Semantic search using FAISS vector database
  - BGE-large-en-v1.5 for embeddings
- **LLM Integration**
  - DeepSeek-V3 as the primary language model
  - Together AI for model hosting
- **Observability**
  - LangSmith for tracing and monitoring
  - Comprehensive logging system
- **API Layer**
  - FastAPI for high-performance API endpoints
  - Streaming responses for real-time updates
  - CORS support for frontend integration

#### Frontend (React/Next.js)
- **User Interface**
  - Modern, responsive design with Tailwind CSS
  - Split-pane layout with chat and preview
  - Real-time website preview
  - Interactive chat interface
- **State Management**
  - React hooks for state management
  - Context API for global state
- **Styling**
  - Tailwind CSS for utility-first styling
  - Custom components and animations
  - Responsive design for all devices

## Technology Stack

### AI & ML Components
- **RAG Framework**: LangChain
- **Vector Database**: FAISS
- **Embedding Model**: BGE-large-en-v1.5
- **Language Model**: DeepSeek-V3
- **Observability**: LangSmith
- **Model Hosting**: Together AI

### Frontend Technologies
- **Framework**: Next.js
- **UI Library**: React
- **Styling**: Tailwind CSS
- **Icons**: Font Awesome, Heroicons
- **Animations**: Animate.css

### Backend Technologies
- **Framework**: FastAPI
- **Language**: Python
- **Document Processing**: PyPDF
- **Vector Storage**: FAISS
- **API Integration**: Together AI, LangSmith

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn
- Together AI API key
- LangSmith API key

### Frontend Setup

1. Navigate to the project root directory.

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Backend Setup

1. Create a `.env` file in the backend directory with your API keys:
   ```
   TOGETHER_API_KEY=your_together_api_key
   LANGSMITH_API_KEY=your_langsmith_api_key
   LANGSMITH_ENDPOINT=https://api.smith.langchain.com
   LANGSMITH_TRACING=true
   LANGSMITH_PROJECT=your_project_name
   ```

2. Navigate to the backend directory:
   ```bash
   cd backend
   ```

3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Start the backend server:
   ```bash
   python main.py
   ```

## Usage

1. Place your PDF documents in the `backend/data` directory
2. Start both the backend and frontend servers
3. Open the application in your browser
4. Use the chat interface to instruct the AI to create websites
5. View the generated website in real-time in the preview pane

## Development

### Project Structure

```
.
├── backend/
│   ├── data/           # PDF documents for RAG
│   ├── faiss_index/    # Vector database
│   ├── rag/            # RAG implementation
│   ├── main.py         # FastAPI application
│   └── requirements.txt
├── src/
│   ├── app/           # Next.js pages
│   ├── components/    # React components
│   └── utils/         # Utility functions
└── README.md
```

### Adding Documents

1. Place PDF files in the `backend/data` directory
2. The system will automatically process and index them
3. The content will be available for website generation

### Customization

- Modify the system prompt in `rag_service.py` to change the website generation style
- Adjust the chunk size and overlap in `document_processor.py` for different document types
- Customize the UI components in the `src/components` directory