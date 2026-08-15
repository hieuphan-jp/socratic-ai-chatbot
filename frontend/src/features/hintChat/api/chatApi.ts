import { api as client } from '@/shared/api/client'
import type {
  ChatSession,
  ChatMessage,
  SendMessagePayload,
  ConfirmParentPayload,
  GraphData,
  Topic,
  KnowledgeNodeSummary,
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

  // 7. ルート直下のTopic一覧取得(フォルダ階層のドリルダウン起点)
  // VI: Lấy danh sách Topic ở gốc (điểm bắt đầu duyệt sâu dần theo cấp bậc thư mục)
  getRootTopics: async () => {
    const res = await client.get<Topic[]>('/topics/?parent=null')
    return res
  },

  // 8. 指定Topic直下の子Topic・知識ノードを取得(フォルダを開く操作に相当)
  // VI: Lấy Topic con và knowledge node trực thuộc Topic chỉ định (tương ứng thao tác mở thư mục)
  getTopicChildren: async (topicId: string) => {
    const res = await client.get<{ topics: Topic[]; nodes: KnowledgeNodeSummary[] }>(
      `/topics/${topicId}/children/`
    )
    return res
  },

  // 9. Topic新規作成(parentIdを渡すと、そのTopic配下にネストした子Topicとして作成される)
  // VI: Tạo Topic mới (truyền parentId sẽ tạo thành Topic con lồng dưới Topic đó)
  createTopic: async (name: string, parentId?: string | null) => {
    const res = await client.post<Topic>('/topics/', { name, parent: parentId ?? null })
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