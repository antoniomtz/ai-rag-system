"use client";

import { useState, useRef } from "react";
import Preview from "@/components/Preview";
import { defaultHTML } from "@/utils/consts";

export default function Home() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! I can help you create a website. Just ask me to create a portfolio website or any other type of website you need." },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [previewHtml, setPreviewHtml] = useState(defaultHTML);
  const previewRef = useRef<HTMLDivElement>(null);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          stream: true // Enable streaming
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      let accumulatedContent = '';
      let currentHtml = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Convert the chunk to text
        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                accumulatedContent += parsed.content;
                
                // Try to extract HTML from the accumulated content
                const htmlMatch = accumulatedContent.match(/```html\n([\s\S]*?)\n```/);
                if (htmlMatch) {
                  currentHtml = htmlMatch[1];
                  setPreviewHtml(currentHtml);
                }
              }
            } catch (e) {
              console.error('Error parsing chunk:', e);
            }
          }
        }
      }

      // Add the complete message to the chat
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: accumulatedContent 
      }]);

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: "Sorry, I encountered an error. Please try again." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Chat Panel */}
      <div className="w-1/2 flex flex-col border-r border-gray-200">
        <header className="p-4 bg-white shadow text-xl font-bold">Website Builder Chat</header>
        <main className="flex-1 flex flex-col p-4 overflow-hidden">
          <div className="flex-1 overflow-y-auto flex flex-col gap-2 mb-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg max-w-[90%] ${
                  msg.role === "user"
                    ? "self-end bg-blue-100 text-right"
                    : "self-start bg-gray-100 text-left"
                }`}
              >
                <span className="block text-xs text-gray-500 mb-1">
                  {msg.role === "user" ? "You" : "Assistant"}
                </span>
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            ))}
            {isLoading && (
              <div className="self-start bg-gray-100 text-left p-3 rounded-lg max-w-[90%]">
                <span className="block text-xs text-gray-500 mb-1">Assistant</span>
                <span>Creating your website...</span>
              </div>
            )}
          </div>
          <form onSubmit={handleSend} className="flex gap-2">
            <input
              className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300"
              type="text"
              placeholder="Ask me to create a website..."
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              className={`px-6 py-2 rounded-lg text-white font-medium transition ${
                isLoading 
                  ? "bg-blue-300 cursor-not-allowed" 
                  : "bg-blue-500 hover:bg-blue-600"
              }`}
              disabled={isLoading}
            >
              Send
            </button>
          </form>
        </main>
      </div>

      {/* Preview Panel */}
      <Preview
        html={previewHtml}
        isResizing={false}
        isAiWorking={isLoading}
        setView={() => {}}
        ref={previewRef}
      />
    </div>
  );
}
