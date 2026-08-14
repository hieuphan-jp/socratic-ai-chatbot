/**
 * shared/types/index.ts
 *
 * JA: 複数の feature で共有する型を置く。features 固有の型は各 feature 内に置くこと。
 *     バックエンドのシリアライザ出力と形を合わせる（ズレたら型エラーで気づける）。
 * VI: Đặt các kiểu dùng chung nhiều feature. Kiểu riêng của feature để trong feature đó.
 *     Khớp hình dạng với output serializer backend (lệch sẽ báo lỗi kiểu để phát hiện).
 */

// JA: 現在ユーザー。accounts.UserSerializer と対応。
// VI: User hiện tại, tương ứng accounts.UserSerializer.
export type User = {
  id: number
  username: string
  email: string
}

export type SenderType = 'USER' | 'AI'
export type NodeType = 'STEP' | 'ANSWER' | 'CHANGE_METHOD'

// JA: チャットメッセージ。ChatMessageSerializer と対応。
// VI: Tin nhắn chat, tương ứng ChatMessageSerializer backend.
export type ChatMessage = {
  id: string
  session: string
  parent_message: string | null
  suggested_parent_id?: string | null
  parent_confidence?: 'high' | 'low' | ''
  parent_confirmed?: boolean
  sender: SenderType
  message_text: string
  is_hint: boolean
  node_type: NodeType
  created_at: string
}

// JA: チャットセッション。ChatSessionSerializer と対応。
// VI: Phiên chat, tương ứng ChatSessionSerializer backend.
export type ChatSession = {
  id: string
  user: number
  title: string
  knowledge_node?: number | null
  hint_count?: number
  completed_at?: string | null
  messages?: ChatMessage[]
  created_at: string
}

export type StepNode = {
  id: string
  step_number: number
  label: string
  parentId?: string
  childrenIds?: string[]
}

// JA: メッセージ送信ペイロード。SendMessageInputSerializer と対応。
// VI: Payload gửi tin nhắn, tương ứng SendMessageInputSerializer backend.
export type SendMessagePayload = {
  message_text: string
  parent_message_id?: string | null
  action_type: 'ANSWER' | 'CHANGE_METHOD' | 'HINT' | 'COMPLETE'
}

// JA: 親ノード確認用ペイロード。ConfirmParentInputSerializer と対応。
// VI: Payload xác nhận node cha, tương ứng ConfirmParentInputSerializer backend.
export type ConfirmParentPayload = {
  message_id: string
  parent_message_id?: string | null
}

// JA: React Flow用のグラフデータ型。GET /api/chat-sessions/{id}/graph/ と対応。
// VI: Kiểu dữ liệu Graph cho React Flow, tương ứng GET /api/chat-sessions/{id}/graph/.
export type FlowNode = {
  id: string
  type: string
  data: {
    label: string
    text: string
    node_type: NodeType
  }
}

export type FlowEdge = {
  id: string
  source: string
  target: string
}

export type GraphData = {
  nodes: FlowNode[]
  edges: FlowEdge[]
  step_number?: number       // JA: ステップ番号 / VI: Thứ tự bước (1, 2, 3...)
  label?: string            // JA: ステップの簡潔な概要 / VI: Tóm tắt ngắn gọn của bước
  parentId?: string        // JA: 親ステップID / VI: ID bước trước đó
  childrenIds?: string[]   // JA: 子ステップID群 / VI: Danh sách ID bước con (nếu có chia nhánh)
}

// JA: 学習内容ツリーのノード。GET /api/learning-tree/ と対応。
//     type で「棚(topic)」か「本(knowledge_node)」かを区別する
//     （knowledge_node のみ復習開始(node_id)の対象にできる）。
// VI: Node cây nội dung đã học, tương ứng GET /api/learning-tree/.
//     type phân biệt "kệ" (topic) hay "sách" (knowledge_node)
//     (chỉ knowledge_node mới dùng để bắt đầu ôn tập qua node_id).
export type TreeNode = {
  id: string
  label: string
  type: 'topic' | 'knowledge_node'
  children?: TreeNode[]
}