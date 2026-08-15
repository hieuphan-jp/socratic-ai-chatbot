/**
 * features/hintChat/api/chatApi.ts
 *
 * JA: Django Backendと通信する Hint Chat API クライアント。
 * VI: API Client giao tiếp với Django Backend cho tính năng Hint Chat.
 */

import { api as client } from '@/shared/api/client'
import type { 
  ChatSession, 
  ChatMessage, 
  SendMessagePayload, 
  ConfirmParentPayload, 
  GraphData 
} from '@/shared/types'

export const chatApi = {
  /**
   * JA: チャットセッション一覧を取得
   * VI: 1. Lấy danh sách các phiên chat
   */
  getSessions: async () => {
    const res = await client.get<ChatSession[]>('/chat-sessions/')
    return res
  },

  /**
   * JA: 新しいチャットセッションを作成
   * VI: 2. Tạo phiên chat mới
   */
  createSession: async (title: string = 'New Session', nodeId?: number) => {
    const res = await client.post<ChatSession>('/chat-sessions/', { title, node_id: nodeId })
    return res
  },

  /**
   * JA: メッセージを送信し、AIの返答を受信
   * VI: 3. Gửi tin nhắn và nhận phản hồi từ AI
   */
  sendMessage: async (sessionId: string, payload: SendMessagePayload) => {
    const res = await client.post<{
      user_message: ChatMessage
      ai_message: ChatMessage
      session_info?: {
        hint_count: number
        completed_at: string | null
      }
    }>(`/chat-sessions/${sessionId}/send-message/`, payload)
    return res
  },

  /**
   * JA: 親ノードの確定・変更（分岐処理）
   * VI: 4. Xác nhận / Thay đổi Node cha (Rẽ nhánh)
   */
  confirmParent: async (sessionId: string, payload: ConfirmParentPayload) => {
    const res = await client.post<ChatMessage>(`/chat-sessions/${sessionId}/confirm-parent/`, payload)
    return res
  },

  /**
   * JA: 思考ツリー（React Flow Graph）のデータを取得
   * VI: 5. Lấy dữ liệu sơ đồ cây tư duy (React Flow Graph)
   */
  getGraph: async (sessionId: string) => {
    const res = await client.get<GraphData>(`/chat-sessions/${sessionId}/graph/`)
    return res
  },

  /**
   * JA: 特定セッションのメッセージ一覧を取得
   * VI: 6. Lấy danh sách tin nhắn của một phiên chat
   */
  getMessages: async (sessionId: string) => {
    const res = await client.get<ChatMessage[]>(`/chat-sessions/${sessionId}/messages/`)
    return res
  },
}