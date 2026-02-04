'use client';

import React from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  Handle, 
  Position, 
  NodeProps,
} from '@xyflow/react';
import { useStore } from '@/store/useStore';
import '@xyflow/react/dist/style.css';

const AgentNode = ({ data }: NodeProps) => {
  const statusColors = {
    pending: 'border-zinc-800 bg-zinc-900 text-zinc-600',
    running: 'border-primary bg-primary/10 text-primary animate-pulse shadow-[0_0_15px_rgba(250,204,21,0.4)]',
    done: 'border-success bg-success/10 text-success',
    error: 'border-critical bg-critical/10 text-critical',
  };

  const status = (data.status as keyof typeof statusColors) || 'pending';

  return (
    <div className={`px-4 py-2 rounded-lg border-2 font-mono text-xs min-w-[140px] shadow-lg transition-all duration-500 ${statusColors[status]}`}>
      <Handle type="target" position={Position.Top} className="!bg-slate-700" />
      <div className="flex flex-col items-center">
        <div className="font-bold tracking-tight uppercase">{data.label as string}</div>
        <div className="text-[10px] opacity-70 mt-0.5 capitalize">{status}</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-slate-700" />
    </div>
  );
};

const nodeTypes = {
  agentNode: AgentNode,
};

export const FlowGraph = () => {
  const { status, currentPhase } = useStore();

  const phases = [
    { id: 'normalization', label: 'Normalization' },
    { id: 'reconnaissance', label: 'Reconnaissance' },
    { id: 'scanning', label: 'Scanning' },
    { id: 'exploitation', label: 'Exploitation' },
    { id: 'reporting', label: 'Reporting' },
  ];

  // Map phase labels to status
  const getStatus = (phaseId: string) => {
    const currentIdx = phases.findIndex(p => p.id === currentPhase.toLowerCase() || p.label === currentPhase);
    const thisIdx = phases.findIndex(p => p.id === phaseId);

    if (thisIdx < currentIdx) return 'done';
    if (thisIdx === currentIdx) {
        return status === 'running' ? 'running' : 'done';
    }
    return 'pending';
  };

  const nodes = phases.map((p, i) => ({
    id: p.id,
    type: 'agentNode',
    position: { x: 250, y: i * 100 },
    data: { 
      label: p.label, 
      status: getStatus(p.id) 
    },
  }));

  const edges = phases.slice(0, -1).map((p, i) => ({
    id: `e${i}`,
    source: p.id,
    target: phases[i + 1].id,
    animated: getStatus(phases[i+1].id) === 'running' || getStatus(p.id) === 'running',
  }));

  return (
    <div className="w-full h-full bg-[#1d252d]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#334155" gap={20} />
        <Controls showInteractive={false} className="bg-slate-800 border-slate-700 fill-white" />
      </ReactFlow>
    </div>
  );
};
