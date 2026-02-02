'use client';

import dynamic from 'next/dynamic';
import React, { useState } from 'react';
import { Terminal as TerminalIcon, GitBranch, Play, Square, RefreshCcw } from 'lucide-react';
import { useStore } from '@/store/useStore';

const TerminalComponent = dynamic(
  () => import('./TerminalComponent').then((mod) => mod.TerminalComponent),
  { ssr: false }
);

const FlowGraph = dynamic(
  () => import('./FlowGraph').then((mod) => mod.FlowGraph),
  { ssr: false }
);

export const Stage = () => {
  const [activeTab, setActiveTab] = useState<'terminal' | 'graph'>('terminal');
  const { status, currentPhase, progress, logs } = useStore();

  return (
    <div className="w-[480px] h-full border-l border-border flex flex-col bg-background">
      {/* Tab Switcher */}
      <div className="h-12 border-b border-border flex items-center justify-between px-4 bg-accent/10">
        <div className="flex items-center gap-1 h-full font-mono text-xs">
          <button
            onClick={() => setActiveTab('terminal')}
            className={`px-4 h-full flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'terminal' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <TerminalIcon className="w-3.5 h-3.5" />
            OPERATIONS.LOG
          </button>
          <button
            onClick={() => setActiveTab('graph')}
            className={`px-4 h-full flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'graph' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            AGENT_FLOW.DAG
          </button>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-muted-foreground uppercase leading-none">{currentPhase}</span>
            <div className="w-32 h-1 bg-accent rounded-full mt-1 overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-500" 
                style={{ width: `${progress}%` }} 
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-1.5 rounded bg-primary/10 text-primary hover:bg-primary/20 transition-colors">
              <Play className="w-4 h-4 fill-current" />
            </button>
            <button className="p-1.5 rounded bg-accent text-muted-foreground hover:bg-accent/80 transition-colors">
              <RefreshCcw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 relative overflow-hidden bg-black/20">
        {activeTab === 'terminal' ? (
          <TerminalComponent logs={logs} />
        ) : (
          <FlowGraph />
        )}
      </div>
    </div>
  );
};
