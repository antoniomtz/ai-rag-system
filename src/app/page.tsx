"use client";

import { useState } from "react";

export default function Home() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");

  // Placeholder for sending a message
  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages([...messages, { role: "user", content: input }]);
    setInput("");
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <header className="p-4 bg-white shadow text-xl font-bold text-center">LLM Chat</header>
      <main className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-xl flex flex-col gap-4 bg-white rounded shadow p-4 min-h-[400px]">
          <div className="flex-1 overflow-y-auto flex flex-col gap-2">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-2 rounded max-w-[80%] ${
                  msg.role === "user"
                    ? "self-end bg-blue-100 text-right"
                    : "self-start bg-gray-200 text-left"
                }`}
              >
                <span className="block text-xs text-gray-500 mb-1">
                  {msg.role === "user" ? "You" : "Assistant"}
                </span>
                <span>{msg.content}</span>
              </div>
            ))}
          </div>
          <form onSubmit={handleSend} className="flex gap-2 mt-2">
            <input
              className="flex-1 border rounded px-3 py-2 focus:outline-none focus:ring focus:border-blue-300"
              type="text"
              placeholder="Type your message..."
              value={input}
              onChange={e => setInput(e.target.value)}
            />
            <button
              type="submit"
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
            >
              Send
            </button>
          </form>
        </div>
      </main>
      <footer className="p-2 text-center text-xs text-gray-400">&copy; {new Date().getFullYear()} AI-RAG-System</footer>
    </div>
  );
}
