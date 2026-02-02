'use client';

import { Sidebar } from '@/components/Sidebar';
import { Stage } from '@/components/Stage';
import { Intelligence } from '@/components/Intelligence';
import { ModelSelector } from '@/components/ModelSelector';
import { Command, Search, Bell, Settings, Terminal } from 'lucide-react';

export default function Home() {
  return (
    <main className="flex flex-col h-screen w-screen bg-black text-primary font-sans selection:bg-primary/30">
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-black/80 backdrop-blur-xl z-50">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-yellow-400 to-yellow-700 flex items-center justify-center shadow-lg shadow-primary/20">
              <Terminal className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tighter uppercase italic">Firestarter</span>
          </div>
          <div className="h-4 w-px bg-border mx-2" />
          <nav className="flex items-center gap-6 text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
             <button className="text-primary border-b-2 border-primary py-4 -mb-px">Operations</button>
             <button className="hover:text-foreground transition-colors">Analytics</button>
             <button className="hover:text-foreground transition-colors">Agents</button>
             <button className="hover:text-foreground transition-colors">Settings</button>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <ModelSelector />
          <div className="h-4 w-px bg-border" />
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground group-focus-within:text-primary transition-colors" />
            <input 
              type="text" 
              placeholder="QUICK COMMAND (CMD+K)"
              className="bg-accent/40 border-border border rounded-full pl-9 pr-4 py-1.5 text-[10px] w-64 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all font-mono"
            />
          </div>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-2">
            <button className="p-2 rounded-full hover:bg-accent transition-colors relative">
               <Bell className="w-4 h-4 text-muted-foreground" />
               <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-critical rounded-full" />
            </button>
            <button className="p-2 rounded-full hover:bg-accent transition-colors">
               <Settings className="w-4 h-4 text-muted-foreground" />
            </button>
            <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-[10px] font-bold text-primary">
              OP
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <Intelligence />
        <Stage />
      </div>

      {/* Footer Info Bar */}
      <footer className="h-8 border-t border-border bg-accent/20 flex items-center justify-between px-4 text-[10px] font-mono text-muted-foreground">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-success" />
            <span>SESSION: ACTIVE_SCAN_01</span>
          </div>
          <div>CPU: 12%</div>
          <div>MEM: 4.2GB</div>
        </div>
        <div className="flex items-center gap-4">
          <span>LATENCY: 24ms</span>
          <span className="text-primary font-bold">READY_FOR_COMMAND</span>
        </div>
      </footer>
    </main>
  );
}
