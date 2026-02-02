'use client';

import React, { useState } from 'react';
import { Brain, Zap, History, Database, ChevronRight, MessageSquare, ListFilter } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { Chat } from './Chat';

export const Intelligence = () => {
  const [activeTab, setActiveTab] = useState<'insights' | 'chat'>('insights');
  const { findings } = useStore();

  return (
    <div className="flex-1 h-full bg-background/50 backdrop-blur-md flex flex-col">
      {/* Tab Switcher */}
      <div className="h-12 border-b border-border flex items-center bg-accent/10">
        <button
          onClick={() => setActiveTab('insights')}
          className={`flex-1 h-full flex items-center justify-center gap-2 text-[10px] font-bold uppercase tracking-widest transition-colors ${
            activeTab === 'insights' ? 'text-primary bg-primary/5' : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Brain className="w-3.5 h-3.5" />
          Insights
        </button>
        <div className="w-px h-6 bg-border" />
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex-1 h-full flex items-center justify-center gap-2 text-[10px] font-bold uppercase tracking-widest transition-colors ${
            activeTab === 'chat' ? 'text-primary bg-primary/5' : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          Agent Chat
        </button>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col p-2">
        {activeTab === 'insights' ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Reasoning Section */}
            <div className="p-4 rounded-lg border border-border bg-primary/5 mb-2">
              <div className="flex items-center gap-2 mb-3">
                 <div className="p-1 rounded bg-primary/20">
                   <Zap className="w-3.5 h-3.5 text-primary" />
                 </div>
                 <span className="text-[10px] font-bold uppercase tracking-wider">Active Reasoning</span>
              </div>
              <div className="text-xs font-medium leading-relaxed text-foreground/90 italic">
                "Target application appears to be using a legacy CMS. I am prioritizing scanning for known CVEs related to version 4.2.x while bypassing the basic rate-limiting detected..."
              </div>
            </div>

            {/* Findings List */}
            <div className="flex-1 overflow-hidden flex flex-col rounded-lg border border-border bg-background/40">
              <div className="p-3 border-b border-border flex items-center justify-between bg-accent/10">
                 <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Findings Memory</span>
                 <ListFilter className="w-3.5 h-3.5 opacity-30" />
              </div>
              
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {/* Mock Finding */}
                <div className="p-3 rounded-lg border border-critical/30 bg-critical/5 group cursor-pointer hover:bg-critical/10 transition-colors">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] font-bold text-critical uppercase">Critical</span>
                    <span className="text-[10px] text-muted-foreground font-mono">12:04:33</span>
                  </div>
                  <div className="text-sm font-bold group-hover:text-critical transition-colors">SQL Injection in /api/v1/search</div>
                  <div className="text-xs text-muted-foreground mt-1 line-clamp-2">Confirmed blind SQL injection on parameter 'q'. Full DB access possible.</div>
                </div>

                <div className="p-3 rounded-lg border border-warning/30 bg-warning/5 group cursor-pointer hover:bg-warning/10 transition-colors">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] font-bold text-warning uppercase">Medium</span>
                    <span className="text-[10px] text-muted-foreground font-mono">11:58:21</span>
                  </div>
                  <div className="text-sm font-bold group-hover:text-warning transition-colors">Exposed Docker Socket</div>
                  <div className="text-xs text-muted-foreground mt-1 line-clamp-2">Potential container escape via /var/run/docker.sock.</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <Chat />
        )}
      </div>

      {/* Memory Footer */}
      <div className="p-2 border-t border-border bg-accent/20">
        <button className="w-full py-2 px-4 rounded border border-border bg-background hover:bg-accent text-[10px] flex items-center justify-between transition-colors uppercase font-bold tracking-widest">
          <div className="flex items-center gap-2">
            <Database className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Open Vector Memory</span>
          </div>
          <ChevronRight className="w-3.5 h-3.5 opacity-50" />
        </button>
      </div>
    </div>
  );
};
