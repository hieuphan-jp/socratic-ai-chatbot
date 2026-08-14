import { api as client } from '@/shared/api/client'
import type {
  ChatSession,
  ChatMessage,
  SendMessagePayload,
  ConfirmParentPayload,
  GraphData,
  Topic,
} from '@/shared/types'

export const chatApi = {
  // 1. Lấy danh sách các phiên chat
  getSessions: async () => {
    const res = await client.get<ChatSession[]>('/chat-sessions/')
    return res
  },

  // 2. Tạo phiên chat mới
  createSession: async (title: string = 'New Session', nodeId?: number) => {
    const res = await client.post<ChatSession>('/chat-sessions/', { title, node_id: nodeId })
    return res
  },

  // 3. Gửi tin nhắn và nhận phản hồi từ AI
  sendMessage: async (sessionId: string, payload: SendMessagePayload) => {
    const res = await client.post<{
      user_message: ChatMessage
      ai_message: ChatMessage
      knowledge_node: string | null
      knowledge_node_title: string | null
    }>(`/chat-sessions/${sessionId}/send-message/`, payload)
    return res
  },

  // 7. Topic一覧取得（知識ノードの保存先選択用）/ VI: Lấy danh sách Topic (để chọn nơi lưu knowledge node)
  getTopics: async () => {
    const res = await client.get<Topic[]>('/topics/')
    return res
  },

  // 8. Topic新規作成 / VI: Tạo Topic mới
  createTopic: async (name: string) => {
    const res = await client.post<Topic>('/topics/', { name })
    return res
  },

  // 4. Xác nhận / Thay đổi Node cha (Rẽ nhánh)
  confirmParent: async (sessionId: string, payload: ConfirmParentPayload) => {
    const res = await client.post<ChatMessage>(`/chat-sessions/${sessionId}/confirm-parent/`, payload)
    return res
  },

  // 5. Lấy dữ liệu sơ đồ cây tư duy (React Flow Graph)
  getGraph: async (sessionId: string) => {
    const res = await client.get<GraphData>(`/chat-sessions/${sessionId}/graph/`)
    return res
  },

  // 6. Lấy danh sách tin nhắn của một phiên chat
  getMessages: async (sessionId: string) => {
    const res = await client.get<ChatMessage[]>(`/chat-sessions/${sessionId}/messages/`)
    return res
  },
}