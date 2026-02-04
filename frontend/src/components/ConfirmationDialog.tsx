'use client';

import { useState } from 'react';
import { X, Play, Ban, Edit3, AlertTriangle, Shield, Zap } from 'lucide-react';

interface PendingAction {
    action_id: string;
    tool_name: string;
    target: string;
    command: string;
    description: string;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    estimated_time?: string;
}

interface ConfirmationDialogProps {
    action: PendingAction;
    onConfirm: (approved: boolean, editedCommand?: string) => void;
    onClose: () => void;
}

const riskColors = {
    low: { bg: 'bg-green-500/20', border: 'border-green-500/50', text: 'text-green-400', icon: Shield },
    medium: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', text: 'text-yellow-400', icon: Zap },
    high: { bg: 'bg-orange-500/20', border: 'border-orange-500/50', text: 'text-orange-400', icon: AlertTriangle },
    critical: { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400', icon: AlertTriangle }
};

export default function ConfirmationDialog({ action, onConfirm, onClose }: ConfirmationDialogProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [editedCommand, setEditedCommand] = useState(action.command);
    
    const riskStyle = riskColors[action.risk_level];
    const RiskIcon = riskStyle.icon;

    const handleApprove = () => {
        if (isEditing) {
            onConfirm(true, editedCommand);
        } else {
            onConfirm(true);
        }
    };

    const handleReject = () => {
        onConfirm(false);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-lg mx-4 bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl overflow-hidden">
                {/* Header */}
                <div className={`px-6 py-4 ${riskStyle.bg} border-b ${riskStyle.border}`}>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <RiskIcon className={`w-6 h-6 ${riskStyle.text}`} />
                            <div>
                                <h2 className="text-lg font-semibold text-white">Action Confirmation</h2>
                                <p className={`text-sm ${riskStyle.text} capitalize`}>
                                    {action.risk_level} Risk
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5 text-zinc-400" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    {/* Tool & Target */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs text-zinc-500 uppercase tracking-wider">Tool</label>
                            <p className="text-white font-mono mt-1">{action.tool_name}</p>
                        </div>
                        <div>
                            <label className="text-xs text-zinc-500 uppercase tracking-wider">Target</label>
                            <p className="text-cyan-400 font-mono mt-1">{action.target}</p>
                        </div>
                    </div>

                    {/* Description */}
                    <div>
                        <label className="text-xs text-zinc-500 uppercase tracking-wider">Description</label>
                        <p className="text-zinc-300 mt-1">{action.description}</p>
                    </div>

                    {/* Command */}
                    <div>
                        <div className="flex items-center justify-between mb-1">
                            <label className="text-xs text-zinc-500 uppercase tracking-wider">Command</label>
                            <button
                                onClick={() => setIsEditing(!isEditing)}
                                className={`flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors ${
                                    isEditing 
                                        ? 'bg-cyan-500/20 text-cyan-400' 
                                        : 'hover:bg-zinc-800 text-zinc-400'
                                }`}
                            >
                                <Edit3 className="w-3 h-3" />
                                {isEditing ? 'Editing' : 'Edit'}
                            </button>
                        </div>
                        {isEditing ? (
                            <textarea
                                value={editedCommand}
                                onChange={(e) => setEditedCommand(e.target.value)}
                                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded-lg font-mono text-sm text-green-400 focus:outline-none focus:border-cyan-500 resize-none"
                                rows={3}
                            />
                        ) : (
                            <div className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg font-mono text-sm text-green-400 overflow-x-auto">
                                {action.command}
                            </div>
                        )}
                    </div>

                    {/* Estimated Time */}
                    {action.estimated_time && (
                        <div>
                            <label className="text-xs text-zinc-500 uppercase tracking-wider">Estimated Time</label>
                            <p className="text-zinc-300 mt-1">{action.estimated_time}</p>
                        </div>
                    )}
                </div>

                {/* Actions */}
                <div className="px-6 py-4 bg-zinc-800/50 border-t border-zinc-700 flex items-center justify-end gap-3">
                    <button
                        onClick={handleReject}
                        className="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/50 rounded-lg transition-colors"
                    >
                        <Ban className="w-4 h-4" />
                        Reject
                    </button>
                    <button
                        onClick={handleApprove}
                        className="flex items-center gap-2 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/50 rounded-lg transition-colors"
                    >
                        <Play className="w-4 h-4" />
                        {isEditing ? 'Run Edited' : 'Approve'}
                    </button>
                </div>
            </div>
        </div>
    );
}
