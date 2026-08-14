// Kiểu dữ liệu Tin nhắn (Chat Message) khớp 100% với Django Backend
export interface ChatMessage {
  id: string;
  session?: string;
  sender: 'AI' | 'USER' | 'ai' | 'user'; // Hỗ trợ cả chữ hoa từ BE
  message_text: string;                  // Tên trường từ BE là message_text
  created_at?: string;
  text?: string;                          // Trường dự phòng FE
  timestamp?: string;                     // Trường dự phòng FE
  is_hint?: boolean;
  node_type?: string;
}

// Kiểu dữ liệu Phiên Chat (Chat Session) từ Django
export interface ChatSession {
  id: string;
  user?: number;
  title: string;
  knowledge_node?: number | null;
  hint_count?: number;
  completed_at?: string | null;
  created_at?: string;
  messages?: ChatMessage[];
}

export type MainTab = 'hintChat' | 'learningTree';

export interface SendMessagePayload {
  message: string;
  node_id?: number;
}

export interface ConfirmParentPayload {
  parent_node_id: number;
}

export interface StepNode {
  id: string;
  label: string;
  labelJp?: string;
  status: 'completed' | 'in_progress' | 'pending';
}

export interface GraphData {
  nodes: StepNode[];
  edges?: Array<{
    id: string;
    source: string;
    target: string;
  }>;
}