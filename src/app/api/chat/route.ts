import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Get the request body
    const body = await request.json();

    // Forward the request to the Python backend
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // If the backend returns an error, throw it
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get response from backend');
    }

    // For streaming responses, we need to handle the response differently
    if (body.stream) {
      // Create a new ReadableStream to transform the backend response
      const stream = new ReadableStream({
        async start(controller) {
          const reader = response.body?.getReader();
          if (!reader) {
            controller.error('No reader available');
            return;
          }

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              // Forward the chunk as is
              controller.enqueue(value);
            }
            controller.close();
          } catch (error) {
            controller.error(error);
          }
        },
      });

      // Return the stream with appropriate headers
      return new NextResponse(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    }

    // For non-streaming responses, return the JSON response
    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error in chat API route:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
} 