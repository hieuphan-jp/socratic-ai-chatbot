export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
}

export interface StepNode {
  id: string;
  label: string;
  labelJp?: string;
  description?: string;
  status: 'completed' | 'in_progress' | 'pending';
}