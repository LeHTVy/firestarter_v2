'use client';

import React from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  Handle, 
  Position, 
  NodeProps,
  BaseEdge,
  EdgeProps,
  getBezierPath,
} from '@xyflow/react';
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

const initialNodes = [
  { id: '1', type: 'agentNode', position: { x: 250, y: 0 }, data: { label: 'Target Normalize', status: 'done' } },
  { id: '2', type: 'agentNode', position: { x: 250, y: 100 }, data: { label: 'Recon Agent', status: 'running' } },
  { id: '3', type: 'agentNode', position: { x: 250, y: 200 }, data: { label: 'Scan Agent', status: 'pending' } },
  { id: '4', type: 'agentNode', position: { x: 250, y: 300 }, data: { label: 'Vuln Agent', status: 'pending' } },
  { id: '5', type: 'agentNode', position: { x: 250, y: 400 }, data: { label: 'Report Agent', status: 'pending' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e2-3', source: '2', target: '3' },
  { id: 'e3-4', source: '3', target: '4' },
  { id: 'e4-5', source: '4', target: '5' },
];

const nodeTypes = {
  agentNode: AgentNode,
};

export const FlowGraph = () => {
  return (
    <div className="w-full h-full bg-[#1d252d]">
      <ReactFlow
        nodes={initialNodes}
        edges={initialEdges}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#334155" gap={20} />
        <Controls showInteractive={false} className="bg-slate-800 border-slate-700 fill-white" />
      </ReactFlow>
    </div>
  );
};
