# AI Chat Application

A chat application built with Next.js frontend and FastAPI backend, using Together AI for generating responses.

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── main.py       # Backend server code
│   ├── requirements.txt  # Python dependencies
│   └── .env         # Environment variables (create this)
├── src/              # Next.js frontend
│   └── app/         # Frontend application code
└── README.md        # This file
```

## Backend Setup

### 1. Create and Activate Virtual Environment

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Make sure you're in the backend directory with venv activated
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

1. Create a `.env` file in the backend directory:
```bash
touch .env
```

2. Add your Together AI API key to the `.env` file:
```
TOGETHER_API_KEY=your_api_key_here
```

You can get your API key from [Together AI](https://www.together.ai/).

### 4. Run the Backend Server

```bash
# Make sure you're in the backend directory with venv activated
python main.py
```

The server will start on `http://localhost:8000`.

## Frontend Setup

### 1. Install Dependencies

```bash
# Navigate to the project root
npm install
```

### 2. Run the Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Running the Application

1. Start the backend server (in the backend directory):
```bash
source venv/bin/activate  # If not already activated
python main.py
```

2. In a new terminal, start the frontend (in the project root):
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:3000`

## API Endpoints

### Chat Endpoint

- **URL**: `/api/chat`
- **Method**: `POST`
- **Request Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Your message here"
    }
  ]
}
```
- **Response**:
```json
{
  "role": "assistant",
  "content": "AI response here"
}
```

## Development

- Backend: FastAPI with Python 3.12+
- Frontend: Next.js 14 with React
- AI: Together AI API

### TypeScript Files

- `next-env.d.ts`: This is an automatically generated TypeScript declaration file for Next.js. 
  - Don't modify it manually
  - Keep it in your project
  - It's automatically managed by Next.js
  - It's included in `.gitignore` by default

## Notes

- Make sure to keep your API key secure and never commit it to version control
- The backend server must be running for the frontend to work properly
- The application uses CORS to allow communication between frontend and backend