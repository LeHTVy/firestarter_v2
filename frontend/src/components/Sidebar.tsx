'use client';

import React from 'react';
import { useStore } from '@/store/useStore';
import { Target, Shield, Globe, Network, ChevronRight } from 'lucide-react';

export const Sidebar = () => {
  const { selectedTarget, setTarget } = useStore();

  const targets = [
    { id: '1', name: 'example.com', type: 'domain', nodes: ['sub1.example.com', 'sub2.example.com'] },
    { id: '2', name: '192.168.1.0/24', type: 'network', nodes: ['192.168.1.1', '192.168.1.45'] },
  ];

  return (
    <div className="w-80 h-full border-r border-border bg-background/50 backdrop-blur-md flex flex-col">
      <div className="p-4 border-b border-border flex items-center gap-2">
        <Shield className="w-5 h-5 text-primary" />
        <h2 className="font-bold text-sm tracking-widest uppercase">Attack Surface</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {targets.map((t) => (
          <div key={t.id} className="group">
            <button
              onClick={() => setTarget(t.name)}
              className={`w-full flex items-center gap-2 p-2 rounded-md text-sm transition-colors ${
                selectedTarget === t.name ? 'bg-primary/10 text-primary' : 'hover:bg-accent/50'
              }`}
            >
              {t.type === 'domain' ? <Globe className="w-4 h-4" /> : <Network className="w-4 h-4" />}
              <span className="flex-1 text-left truncate">{t.name}</span>
              <ChevronRight className="w-3 h-3 opacity-50 group-hover:opacity-100 transition-opacity" />
            </button>
            
            {selectedTarget === t.name && (
              <div className="ml-6 mt-1 space-y-1 border-l border-primary/20 pl-4 py-1">
                {t.nodes.map((node) => (
                  <button
                    key={node}
                    className="w-full text-xs text-muted-foreground hover:text-foreground text-left py-1 transition-colors"
                  >
                    {node}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-border bg-accent/20">
        <div className="text-[10px] text-muted-foreground uppercase mb-2">System Status</div>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span>Core Engine: Connected</span>
        </div>
      </div>
    </div>
  );
};
