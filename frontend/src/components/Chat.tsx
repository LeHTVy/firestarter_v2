'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '@/store/useStore';
import { Send, User, Bot, Sparkles } from 'lucide-react';

export const Chat = () => {
  const { messages, sendMessage } = useStore();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const currentInput = input;
    setInput('');
    await sendMessage(currentInput);
  };

  return (
    <div className="flex flex-col h-full bg-background/30 rounded-lg border border-border overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
              msg.role === 'user' ? 'bg-primary/20 text-primary' : 'bg-purple-600/20 text-purple-400'
            }`}>
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div className={`max-w-[80%] rounded-2xl p-3 text-sm ${
              msg.role === 'user' 
                ? 'bg-primary/10 text-foreground border border-primary/20 rounded-tr-none' 
                : 'bg-accent/40 text-foreground/90 border border-border rounded-tl-none'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 border-t border-border bg-accent/10">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask agent about findings..."
            className="w-full bg-background border border-border rounded-full pl-4 pr-12 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all"
          />
          <button
            onClick={handleSend}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="mt-2 flex items-center gap-2 px-1">
          <Sparkles className="w-3 h-3 text-primary animate-pulse" />
          <span className="text-[10px] text-muted-foreground italic">Agent is ready to analyze context...</span>
        </div>
      </div>
    </div>
  );
};
