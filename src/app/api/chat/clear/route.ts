import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Forward the request to the Python backend
    const response = await fetch(`${BACKEND_URL}/api/chat/clear`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // If the backend returns an error, throw it
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to clear chat context');
    }

    // Return the success response
    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error in clear chat API route:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
} 