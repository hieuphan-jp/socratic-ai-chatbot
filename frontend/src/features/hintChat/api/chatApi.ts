import { api as client } from '@/shared/api/client'
import type { ChatSession, ChatMessage, SendMessagePayload, GraphData } from '@/shared/types'

export const chatApi = {
  // 1. Lấy danh sách các phiên chat
  getSessions: async () => {
    const res = await client.get<ChatSession[]>('/chat-sessions/')
    return res
  },

  // 2. Tạo phiên chat mới
  createSession: async (title: string = 'New Session') => {
    const res = await client.post<ChatSession>('/chat-sessions/', { title })
    return res
  },

  // 3. Gửi tin nhắn và nhận phản hồi từ AI
  sendMessage: async (sessionId: string, payload: SendMessagePayload) => {
    const res = await client.post<{
      user_message: ChatMessage
      ai_message: ChatMessage
    }>(`/chat-sessions/${sessionId}/send-message/`, payload)
    return res
  },

  // 4. Lấy dữ liệu sơ đồ cây tư duy (React Flow Graph)
  getGraph: async (sessionId: string) => {
    const res = await client.get<GraphData>(`/chat-sessions/${sessionId}/graph/`)
    return res
  },
}