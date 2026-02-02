'use client';

import React, { useState } from 'react';
import { useStore } from '@/store/useStore';
import { ChevronDown, Cpu, Check, Zap, Layers, Settings2, Target, Search, BarChart3 } from 'lucide-react';

export const ModelSelector = () => {
  const { 
    currentModel, 
    availableModels, 
    operationalMode, 
    agentBrainMapping,
    setModel, 
    setMode,
    updateAgentBrain,
    fetchModels 
  } = useStore();
  
  const [isOpen, setIsOpen] = useState(false);

  React.useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const roles = [
    { id: 'recon' as const, label: 'Recon Agent', icon: Search, desc: 'Information gathering & scanning' },
    { id: 'exploit' as const, label: 'Exploit Agent', icon: Target, desc: 'Vulnerability analysis & exploitation' },
    { id: 'analytic' as const, label: 'Analytic Agent', icon: BarChart3, desc: 'Strategy & report generation' }
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent/30 border border-border hover:bg-accent/50 transition-all active:scale-95"
      >
        <div className="p-1 rounded bg-primary/20">
          {operationalMode === 'multi-agent' ? (
            <Layers className="w-3.5 h-3.5 text-primary" />
          ) : (
            <Zap className="w-3.5 h-3.5 text-primary" />
          )}
        </div>
        <div className="flex flex-col items-start leading-tight">
          <span className="text-[10px] font-bold uppercase tracking-wider">
            {operationalMode === 'multi-agent' ? 'Multi-Agent Mode' : 'Quick Mode'}
          </span>
          <span className="text-[8px] opacity-50 font-mono">
            {operationalMode === 'multi-agent' ? 'Optimized Chaining' : currentModel}
          </span>
        </div>
        <ChevronDown className={`w-3 h-3 transition-transform ml-1 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full mt-2 right-0 w-80 bg-popover border border-border rounded-lg shadow-2xl z-50 animate-in fade-in zoom-in duration-200 overflow-hidden flex flex-col">
            
            {/* Mode SwitcherTabs */}
            <div className="flex p-1 bg-accent/20 border-b border-border">
              <button 
                onClick={() => setMode('quick')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded text-[10px] font-bold uppercase tracking-wider transition-all ${
                  operationalMode === 'quick' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Zap className="w-3 h-3" />
                Quick
              </button>
              <button 
                onClick={() => setMode('multi-agent')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded text-[10px] font-bold uppercase tracking-wider transition-all ${
                  operationalMode === 'multi-agent' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Layers className="w-3 h-3" />
                Multi-Agent
              </button>
            </div>

            <div className="max-h-[400px] overflow-y-auto">
              {operationalMode === 'quick' ? (
                <div className="py-2">
                  <div className="px-3 py-1 mb-1">
                    <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest">Select Direct Brain</span>
                  </div>
                  {availableModels.length === 0 ? (
                    <div className="px-3 py-4 text-center">
                      <p className="text-[10px] text-muted-foreground italic">No models found in Ollama.</p>
                      <p className="text-[8px] text-muted-foreground mt-1">Check if Ollama is running.</p>
                    </div>
                  ) : (
                    availableModels.filter(m => m !== 'Multi-Model').map((model) => (
                      <button
                        key={model}
                        onClick={() => {
                          setModel(model);
                          setIsOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2.5 text-xs transition-all hover:bg-primary/5 ${
                          currentModel === model ? 'text-primary' : 'text-foreground/70'
                        }`}
                      >
                        <span className="font-medium underline-offset-4">{model}</span>
                        {currentModel === model && <Check className="w-3.5 h-3.5" />}
                      </button>
                    ))
                  )}
                </div>
              ) : (
                <div className="p-3 space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-1">
                      <Settings2 className="w-3 h-3" />
                      Orchestrator Config
                    </span>
                  </div>
                  
                  {availableModels.length === 0 ? (
                    <div className="p-4 text-center bg-accent/10 rounded-md border border-dashed border-border">
                      <p className="text-[10px] text-muted-foreground italic">Connect to Ollama to configure agents.</p>
                    </div>
                  ) : (
                    roles.map((role) => (
                      <div key={role.id} className="space-y-1.5 p-2 rounded-md bg-accent/10 border border-border/50">
                        <div className="flex items-center gap-2">
                          <role.icon className="w-3 h-3 text-primary/70" />
                          <span className="text-[10px] font-bold uppercase tracking-widest">{role.label}</span>
                        </div>
                        <p className="text-[10px] text-muted-foreground leading-tight px-1">{role.desc}</p>
                        
                        <select 
                          className="w-full bg-background border border-border rounded px-2 py-1.5 text-[10px] font-mono focus:outline-none focus:ring-1 focus:ring-primary/50 cursor-pointer"
                          value={agentBrainMapping[role.id]}
                          onChange={(e) => updateAgentBrain(role.id, e.target.value)}
                        >
                          {availableModels.filter(m => m !== 'Multi-Model').map(m => (
                            <option key={m} value={m}>{m}</option>
                          ))}
                        </select>
                      </div>
                    ))
                  )}
                  
                  <div className="pt-2">
                    <button 
                      onClick={() => setIsOpen(false)}
                      disabled={availableModels.length === 0}
                      className="w-full py-2 bg-primary/10 hover:bg-primary/20 disabled:opacity-30 disabled:cursor-not-allowed text-primary text-[10px] font-bold uppercase tracking-widest rounded transition-colors"
                    >
                      Deploy Architecture
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
