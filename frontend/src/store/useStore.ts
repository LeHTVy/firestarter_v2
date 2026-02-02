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

interface AgentState {
    status: 'idle' | 'running' | 'error' | 'finished';
    currentPhase: string;
    progress: number;
    logs: string[];
    findings: Finding[];
    messages: Message[];
    availableModels: string[];
    currentModel: string;
    selectedTarget: string | null;

    // Actions
    setStatus: (status: AgentState['status']) => void;
    setPhase: (phase: string) => void;
    setProgress: (progress: number) => void;
    addLog: (log: string) => void;
    addFinding: (finding: Finding) => void;
    addMessage: (message: Message) => void;
    setModel: (model: string) => void;
    setTarget: (target: string | null) => void;
    fetchModels: () => Promise<void>;
    sendMessage: (content: string) => Promise<void>;
}

export const useStore = create<AgentState>((set) => ({
    status: 'idle',
    currentPhase: 'Ready',
    progress: 0,
    logs: [],
    findings: [],
    messages: [
        { id: '1', role: 'agent', content: 'Hello! I am Firestarter Agent. How can I assist you with your security assessment today?', timestamp: new Date().toISOString() }
    ],
    availableModels: ['Multi-Model'],
    currentModel: 'Multi-Model',
    selectedTarget: null,

    setStatus: (status) => set({ status }),
    setPhase: (phase) => set({ currentPhase: phase }),
    setProgress: (progress) => set({ progress }),
    addLog: (log) => set((state) => ({ logs: [...state.logs.slice(-1000), log] })),
    addFinding: (finding) => set((state) => ({ findings: [finding, ...state.findings] })),
    addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
    setModel: (model) => set({ currentModel: model }),
    setTarget: (target) => set({ selectedTarget: target }),
    fetchModels: async () => {
        const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
        const apiUrl = `http://${hostname}:8000`;
        try {
            const response = await fetch(`${apiUrl}/api/models`);
            if (response.ok) {
                const data = await response.json();
                const models = data.models.map((m: any) => m.name);
                set((state) => ({
                    availableModels: ['Multi-Model', ...models]
                }));
            }
        } catch (error) {
            console.warn('Backend not detected. Falling back to Ollama direct.');
            try {
                const response = await fetch('http://localhost:11434/api/tags');
                if (response.ok) {
                    const data = await response.json();
                    const models = data.models.map((m: any) => m.name);
                    set((state) => ({
                        availableModels: ['Multi-Model', ...models]
                    }));
                }
            } catch (ollamaError) {
                set((state) => ({ availableModels: ['Multi-Model'] }));
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
            const response = await fetch(`${apiUrl}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [{ role: 'user', content }],
                    model: useStore.getState().currentModel
                })
            });

            if (response.ok) {
                const data = await response.json();
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
}));
