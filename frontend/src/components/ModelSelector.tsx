'use client';

import React, { useState } from 'react';
import { useStore } from '@/store/useStore';
import { ChevronDown, Cpu, Check } from 'lucide-react';

export const ModelSelector = () => {
  const { currentModel, availableModels, setModel, fetchModels } = useStore();
  const [isOpen, setIsOpen] = useState(false);

  React.useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent/30 border border-border hover:bg-accent/50 transition-colors"
      >
        <Cpu className="w-3.5 h-3.5 text-primary" />
        <span className="text-[10px] font-bold uppercase tracking-wider">{currentModel}</span>
        <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 right-0 w-56 bg-popover border border-border rounded-lg shadow-2xl py-1 z-50 animate-in fade-in zoom-in duration-200">
            <div className="px-3 py-2 border-b border-border/50 mb-1">
              <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest">Select Agent Brain</span>
            </div>
            {availableModels.map((model) => (
              <button
                key={model}
                onClick={() => {
                  setModel(model);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 text-xs transition-all hover:bg-primary/10 ${
                  currentModel === model ? 'text-primary bg-primary/10' : 'text-foreground/70'
                }`}
              >
                <div className="flex flex-col items-start">
                  <span className="font-medium underline-offset-4 decoration-primary/30 group-hover:underline">{model}</span>
                  {model === 'Multi-Model' && (
                    <span className="text-[8px] text-primary/50 font-bold uppercase tracking-tighter">Powered by Multi-Agent Orchestrator</span>
                  )}
                </div>
                {currentModel === model && <Check className="w-3.5 h-3.5" />}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
