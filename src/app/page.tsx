"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import Preview from "@/components/Preview";
import { defaultHTML } from "@/utils/consts";
import { FaWandMagicSparkles, FaTrash } from "react-icons/fa6";
import { Inter, Playfair_Display } from "next/font/google";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair" });

export default function Home() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! I can help you create a website. Just ask me to create a portfolio website or any other type of website you need." },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [previewHtml, setPreviewHtml] = useState(defaultHTML);
  const [isResizing, setIsResizing] = useState(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState(35); // percentage
  const previewRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true);
    e.preventDefault();
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const newLeftPanelWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
    
    // Limit the minimum and maximum width of the left panel
    if (newLeftPanelWidth >= 30 && newLeftPanelWidth <= 70) {
      setLeftPanelWidth(newLeftPanelWidth);
    }
  }, [isResizing]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  // Add and remove event listeners
  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

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
                // First try to find HTML in code blocks
                const htmlMatch = accumulatedContent.match(/```html\n([\s\S]*?)\n```/);
                if (htmlMatch) {
                  currentHtml = htmlMatch[1];
                  setPreviewHtml(currentHtml);
                } else {
                  // If no code block found, look for direct HTML content
                  const directHtmlMatch = accumulatedContent.match(/(?:<!DOCTYPE html>|<html[\s\S]*?>)[\s\S]*?(?:<\/html>|$)/i);
                  if (directHtmlMatch) {
                    currentHtml = directHtmlMatch[0];
                    setPreviewHtml(currentHtml);
                  }
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

  const handleClearAll = async () => {
    // Clear chat messages except the initial greeting
    setMessages([
      { role: "assistant", content: "Hello! I can help you create a website. Just ask me to create a portfolio website or any other type of website you need." }
    ]);
    // Reset website preview to default
    setPreviewHtml(defaultHTML);
    // Clear input
    setInput("");
    // Clear backend context
    try {
      await fetch('http://localhost:8000/api/chat/clear', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error clearing context:', error);
    }
  };

  return (
    <div 
      ref={containerRef}
      className={`flex h-screen bg-gray-50 ${inter.variable} ${playfair.variable} relative`}
    >
      {/* Chat Panel */}
      <div 
        className="flex flex-col border-r border-gray-200 bg-white"
        style={{ width: `${leftPanelWidth}%` }}
      >
        <header className="p-6 bg-[#1A1F71] text-white shadow-lg flex justify-between items-center">
          <h1 className="font-playfair text-3xl font-bold tracking-tight">
            Website Builder
            <span className="text-[#fdbb0a] ml-2">✨</span>
          </h1>
          <button
            onClick={handleClearAll}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-sm font-medium"
            title="Clear chat and website"
          >
            <FaTrash className="text-sm" />
            Clear All
          </button>
        </header>
        <main className="flex-1 flex flex-col p-6 overflow-hidden">
          <div className="flex-1 overflow-y-auto flex flex-col gap-3 mb-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl max-w-[90%] shadow-sm ${
                  msg.role === "user"
                    ? "self-end bg-[#1A1F71] text-white"
                    : "self-start bg-gray-50 border border-gray-100"
                }`}
              >
                <span className={`block text-xs mb-1 ${
                  msg.role === "user" ? "text-gray-200" : "text-gray-500"
                }`}>
                  {msg.role === "user" ? "You" : "Assistant"}
                </span>
                <div className="whitespace-pre-wrap font-inter">
                  {msg.role === "assistant" ? (
                    (() => {
                      // First try to find HTML in code blocks
                      const codeMatch = msg.content.match(/```html\n([\s\S]*?)```/);
                      if (codeMatch) {
                        return (
                          <SyntaxHighlighter
                            language="html"
                            style={vscDarkPlus}
                            customStyle={{ borderRadius: 8, fontSize: 14, margin: '12px 0' }}
                            showLineNumbers
                          >
                            {codeMatch[1]}
                          </SyntaxHighlighter>
                        );
                      }
                      
                      // If no code block found, look for direct HTML content
                      const directHtmlMatch = msg.content.match(/(?:<!DOCTYPE html>|<html[\s\S]*?>)[\s\S]*?(?:<\/html>|$)/i);
                      if (directHtmlMatch) {
                        return (
                          <SyntaxHighlighter
                            language="html"
                            style={vscDarkPlus}
                            customStyle={{ borderRadius: 8, fontSize: 14, margin: '12px 0' }}
                            showLineNumbers
                          >
                            {directHtmlMatch[0]}
                          </SyntaxHighlighter>
                        );
                      }
                      
                      return msg.content;
                    })()
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="self-start bg-gray-50 border border-gray-100 text-left p-4 rounded-xl max-w-[90%] shadow-sm">
                <span className="block text-xs text-gray-500 mb-1">Assistant</span>
                <div className="flex items-center gap-2 text-[#1A1F71]">
                  <FaWandMagicSparkles className="animate-spin text-lg text-[#fdbb0a]" />
                  <span className="font-medium">Crafting your website with AI magic...</span>
                </div>
              </div>
            )}
          </div>
          <form onSubmit={handleSend} className="flex gap-3">
            <input
              className="flex-1 border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#1A1F71] focus:border-transparent transition-all font-inter"
              type="text"
              placeholder="Ask me to create a website..."
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              className={`px-6 py-3 rounded-xl text-white font-medium transition-all shadow-sm ${
                isLoading 
                  ? "bg-gray-300 cursor-not-allowed" 
                  : "bg-[#1A1F71] hover:bg-[#1A1F71]/90 active:bg-[#1A1F71]/80"
              }`}
              disabled={isLoading}
            >
              Send
            </button>
          </form>
        </main>
      </div>

      {/* Resizable Divider */}
      <div
        className={`absolute top-0 bottom-0 w-4 cursor-col-resize hover:bg-[#1A1F71]/20 transition-colors flex items-center justify-center ${
          isResizing ? 'bg-[#1A1F71]/30' : 'bg-gray-100'
        }`}
        style={{ left: `${leftPanelWidth}%`, transform: 'translateX(-50%)' }}
        onMouseDown={handleMouseDown}
      >
        <div className="w-1 h-12 bg-gray-300 rounded-full hover:bg-[#1A1F71] transition-colors" />
      </div>

      {/* Preview Panel */}
      <div style={{ width: `${100 - leftPanelWidth}%` }}>
        <Preview
          html={previewHtml}
          isResizing={isResizing}
          isAiWorking={isLoading}
          setView={() => {}}
          ref={previewRef}
        />
      </div>
    </div>
  );
}
