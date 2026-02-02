'use client';

import React, { useEffect, useRef } from 'react';
import { Terminal as XtermTerminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

interface TerminalComponentProps {
  logs: string[];
}

export const TerminalComponent: React.FC<TerminalComponentProps> = ({ logs }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XtermTerminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);

  useEffect(() => {
    if (!terminalRef.current) return;

    let isDisposed = false;

    const term = new XtermTerminal({
      cursorBlink: true,
      fontSize: 12,
      fontFamily: 'JetBrains Mono, monospace',
      theme: {
        background: 'transparent',
        foreground: '#facc15',
        cursor: '#facc15',
        selectionBackground: 'rgba(250, 204, 21, 0.3)',
        black: '#000000',
        red: '#ef4444',
        green: '#10b981',
        yellow: '#facc15',
        blue: '#3b82f6',
        magenta: '#facc15',
        cyan: '#06b6d4',
        white: '#facc15',
      },
      allowTransparency: true,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    
    term.open(terminalRef.current);
    
    // Use requestAnimationFrame for a more reliable initial fit
    const fitTerminal = () => {
      if (isDisposed || !term.element || !term.element.closest('body')) return;
      
      try {
        const rect = terminalRef.current?.getBoundingClientRect();
        if (rect && rect.width > 0 && rect.height > 0) {
          // Xterm 5.0+ internal checks
          // @ts-ignore
          const core = term._core;
          if (core && core._renderService && core._renderService.dimensions) {
            fitAddon.fit();
          }
        }
      } catch (e) {
        // Silently fail as this is frequently a timing issue in React
      }
    };

    // Small delay to ensure xterm renderer is initialized
    const timer = setTimeout(() => {
      requestAnimationFrame(fitTerminal);
    }, 100);

    xtermRef.current = term;
    fitAddonRef.current = fitAddon;

    // Connect to WebSocket
    const hostname = window.location.hostname;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${hostname}:8000/ws/terminal`;
    console.log('🔌 Connecting to Terminal WebSocket:', wsUrl);
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('✅ Terminal WebSocket connected');
      term.writeln('\x1b[1;32m[Connected to Firestarter Backend]\x1b[0m');
      term.writeln('');
    };

    socket.onmessage = (event) => {
      term.write(event.data);
    };

    socket.onerror = (error) => {
      console.error('❌ Terminal WebSocket error:', error);
    };

    socket.onclose = (event) => {
      console.warn('🔌 Terminal WebSocket closed:', event.code, event.reason);
      term.writeln('\x1b[1;31m[Disconnected from Backend]\x1b[0m');
    };

    // Handle user input
    term.onData((data) => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(data);
      }
    });

    const resizeObserver = new ResizeObserver(() => {
      requestAnimationFrame(fitTerminal);
    });

    resizeObserver.observe(terminalRef.current);

    return () => {
      isDisposed = true;
      clearTimeout(timer);
      resizeObserver.disconnect();
      socket.close();
      term.dispose();
      xtermRef.current = null;
    };
  }, []);

  useEffect(() => {
    const term = xtermRef.current;
    if (term && logs.length > 0) {
      const lastLog = logs[logs.length - 1];
      // Only write log fallbacks if it looks like system info
      if (term.element && (lastLog.includes('[Engine]') || lastLog.includes('Status'))) {
        term.writeln(lastLog);
      }
    }
  }, [logs]);

  return (
    <div className="w-full h-full p-2 bg-black/40 backdrop-blur-sm overflow-hidden">
      <div ref={terminalRef} className="w-full h-full" />
    </div>
  );
};
