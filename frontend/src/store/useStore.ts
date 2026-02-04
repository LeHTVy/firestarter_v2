import { create } from 'zustand';

interface Finding {
    id: string;
    type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    title: string;
    description: string;
    timestamp: string;
}

interface Message {
    id: string;
    role: 'user' | 'agent';
    content: string;
    timestamp: string;
}

interface PendingAction {
    action_id: string;
    tool_name: string;
    target: string;
    command: string;
    description: string;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    estimated_time?: string;
}

interface AgentState {
    status: 'idle' | 'running' | 'error' | 'finished';
    currentPhase: string;
    progress: number;
    logs: string[];
    findings: Finding[];
    messages: Message[];
    availableModels: string[];
    currentModel: string;
    operationalMode: 'quick' | 'multi-agent';
    agentMode: 'hitl' | 'auto';  // HITL or Auto mode
    sessionId: string | null;
    pendingAction: PendingAction | null;
    agentBrainMapping: {
        recon: string;
        exploit: string;
        analytic: string;
    };
    selectedTarget: string | null;

    // Actions
    setStatus: (status: AgentState['status']) => void;
    setPhase: (phase: string) => void;
    setProgress: (progress: number) => void;
    addLog: (log: string) => void;
    addFinding: (finding: Finding) => void;
    addMessage: (message: Message) => void;
    setModel: (model: string) => void;
    setMode: (mode: AgentState['operationalMode']) => void;
    setAgentMode: (mode: AgentState['agentMode']) => void;
    setPendingAction: (action: PendingAction | null) => void;
    updateAgentBrain: (role: keyof AgentState['agentBrainMapping'], model: string) => void;
    setTarget: (target: string | null) => void;
    fetchModels: () => Promise<void>;
    sendMessage: (content: string) => Promise<void>;
    confirmAction: (approved: boolean, editedCommand?: string) => Promise<void>;
}

export const useStore = create<AgentState>((set, get) => ({
    status: 'idle',
    currentPhase: 'Ready',
    progress: 0,
    logs: [],
    findings: [],
    messages: [
        { id: '1', role: 'agent', content: 'Hello! I am Firestarter Agent. How can I assist you with your security assessment today?', timestamp: new Date().toISOString() }
    ],
    availableModels: [],
    currentModel: 'Select Model',
    operationalMode: 'quick',
    agentMode: 'hitl',
    sessionId: null,
    pendingAction: null,
    agentBrainMapping: {
        recon: '',
        exploit: '',
        analytic: ''
    },
    selectedTarget: null,

    setStatus: (status) => set({ status }),
    setPhase: (phase) => set({ currentPhase: phase }),
    setProgress: (progress) => set({ progress }),
    addLog: (log) => set((state) => ({ logs: [...state.logs.slice(-1000), log] })),
    addFinding: (finding) => set((state) => ({ findings: [finding, ...state.findings] })),
    addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
    setModel: (model) => set({ currentModel: model }),
    setMode: (mode) => set({ operationalMode: mode }),
    setAgentMode: (mode) => set({ agentMode: mode }),
    setPendingAction: (action) => set({ pendingAction: action }),
    updateAgentBrain: (role, model) => set((state) => ({
        agentBrainMapping: { ...state.agentBrainMapping, [role]: model }
    })),
    setTarget: (target) => set({ selectedTarget: target }),

    fetchModels: async () => {
        const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
        const apiUrl = `http://${hostname}:8000`;
        try {
            const response = await fetch(`${apiUrl}/api/models`);
            if (response.ok) {
                const data = await response.json();
                const modelNames = data.models.map((m: any) => m.name);

                set((state) => {
                    const newMapping = { ...state.agentBrainMapping };
                    let newCurrentModel = state.currentModel;

                    // Populate mapping if empty
                    if (modelNames.length > 0) {
                        if (!newMapping.recon) newMapping.recon = modelNames[0];
                        if (!newMapping.exploit) newMapping.exploit = modelNames[0];
                        if (!newMapping.analytic) newMapping.analytic = modelNames[0];

                        // Set current model if not set or default
                        if (newCurrentModel === 'Select Model' || !modelNames.includes(newCurrentModel)) {
                            newCurrentModel = modelNames[0];
                        }
                    }

                    return {
                        availableModels: modelNames,
                        agentBrainMapping: newMapping,
                        currentModel: newCurrentModel
                    };
                });
            }
        } catch (error) {
            console.warn('Backend not detected. Falling back to Ollama direct.');
            try {
                const response = await fetch('http://localhost:11434/api/tags');
                if (response.ok) {
                    const data = await response.json();
                    const models = data.models.map((m: any) => m.name);
                    set(() => ({
                        availableModels: ['Multi-Model', ...models]
                    }));
                }
            } catch (ollamaError) {
                set(() => ({ availableModels: ['Multi-Model'] }));
            }
        }
    },

    sendMessage: async (content: string) => {
        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content,
            timestamp: new Date().toISOString()
        };

        set((state) => ({ messages: [...state.messages, userMsg] }));

        try {
            const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
            const apiUrl = `http://${hostname}:8000`;
            const state = get();

            const response = await fetch(`${apiUrl}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [{ role: 'user', content }],
                    model: state.currentModel,
                    session_id: state.sessionId,
                    mode: state.agentMode
                })
            });

            if (response.ok) {
                const data = await response.json();

                // Update session ID
                if (data.session_id) {
                    set({ sessionId: data.session_id });
                }

                // Handle confirmation required
                if (data.type === 'confirmation_required' && data.pending_action) {
                    set({ pendingAction: data.pending_action });
                }

                const agentMsg: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'agent',
                    content: data.message.content,
                    timestamp: new Date().toISOString()
                };
                set((state) => ({ messages: [...state.messages, agentMsg] }));
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'agent',
                content: "Error: Could not reach the backend. Please ensure the Python server is running.",
                timestamp: new Date().toISOString()
            };
            set((state) => ({ messages: [...state.messages, errorMsg] }));
        }
    },

    confirmAction: async (approved: boolean, editedCommand?: string) => {
        const state = get();
        if (!state.pendingAction || !state.sessionId) {
            console.error('No pending action or session ID');
            return;
        }

        try {
            const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
            const apiUrl = `http://${hostname}:8000`;

            const response = await fetch(`${apiUrl}/api/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: state.sessionId,
                    action_id: state.pendingAction.action_id,
                    approved,
                    edited_command: editedCommand
                })
            });

            if (response.ok) {
                const data = await response.json();

                // Clear pending action
                set({ pendingAction: null });

                // Add response message
                const agentMsg: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'agent',
                    content: data.message.content,
                    timestamp: new Date().toISOString()
                };
                set((state) => ({ messages: [...state.messages, agentMsg] }));
            }
        } catch (error) {
            console.error('Failed to confirm action:', error);
            set({ pendingAction: null });
        }
    }
}));
