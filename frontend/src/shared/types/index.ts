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

// JA: 1回分の学習・復習の記録。AttemptSerializer と対応。
// VI: Bản ghi một lượt học/ôn tập. Tương ứng AttemptSerializer backend.
export type Attempt = {
  id: string
  hint_count: number
  completed_at: string | null
  created_at: string
}

// JA: チャットセッション。ChatSessionSerializer と対応。
//     【設計変更2026-08-13】hint_count/completed_atはAttemptへ移動したため
//     current_attemptとして返る。knowledge_nodeは1セッションにつき最大1件
//     (OneToOne)。
// VI: Phiên chat, tương ứng ChatSessionSerializer backend.
//     【Thay đổi thiết kế 2026-08-13】hint_count/completed_at đã chuyển sang
//     Attempt nên trả về dưới dạng current_attempt. knowledge_node tối đa 1
//     cho mỗi session (OneToOne).
export type ChatSession = {
  id: string
  user: number
  title: string
  knowledge_node?: string | null
  current_attempt?: Attempt | null
  messages?: ChatMessage[]
  created_at: string
}

// JA: 学習木のカテゴリ(棚)。TopicSerializer と対応。
// VI: Danh mục (kệ) của cây học tập, tương ứng TopicSerializer backend.
export type Topic = {
  id: string
  user: number
  parent: string | null
  name: string
  description: string
  position: number
  created_at: string
  has_children: boolean
}

// JA: 検索・フォルダ表示用の軽量な知識ノード。KnowledgeNodeSummarySerializer と対応。
// VI: Knowledge node dạng gọn dùng cho tìm kiếm/hiển thị thư mục. Tương ứng KnowledgeNodeSummarySerializer.
export type KnowledgeNodeSummary = {
  id: string
  title: string
  topic: string
}

// JA: 知識ノードの詳細(本文つき)。KnowledgeNodeDetailSerializer と対応。
// VI: Chi tiết knowledge node (có nội dung). Tương ứng KnowledgeNodeDetailSerializer.
export type KnowledgeNodeDetail = {
  id: string
  title: string
  content: string
  topic: string
  topic_name: string
}

// JA: 復習スケジュール。ReviewScheduleSerializer と対応。学習木の葉を塗るための
//     材料(色そのものはフロントが決める。CONVENTIONS.md §12 参照)。
//     mastery_level: 緑の濃さ(0〜mastery_max_level、復習回数が増えるほど濃くなる)。
//     is_due: 復習タイミングが来たか(緑の濃さとは別軸、バッジ等に使う)。
//     ReviewSchedule が無い(=このAPIに出てこない)ノードは「未学習」として扱う。
// VI: Lịch ôn tập. Tương ứng ReviewScheduleSerializer. Nguyên liệu để tô màu lá của
//     cây học tập (màu cụ thể do frontend quyết, xem CONVENTIONS.md §12).
//     mastery_level: độ đậm xanh (0 đến mastery_max_level, ôn nhiều thì đậm hơn).
//     is_due: đã tới hạn ôn tập chưa (trục riêng, tách khỏi độ đậm màu, dùng cho badge).
//     Node không có ReviewSchedule (không xuất hiện ở API này) thì coi là "chưa học".
export type ReviewSchedule = {
  id: string
  node_id: string
  node_title: string
  topic_id: string
  interval_days: number
  next_review_at: string
  learned_count: number
  mastery_level: number
  mastery_max_level: number
  is_due: boolean
  days_overdue: number
  chat_session_id: string | null
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
  // JA: COMPLETE時、理解できたかどうかの自己申告(SM-2評価に使われる)。
  // VI: Khi COMPLETE, tự báo cáo có hiểu hay không (dùng để đánh giá SM-2).
  understood?: boolean
  // JA: knowledge_node未設定のセッションをCOMPLETEする時だけ必須(保存先Topic)。
  // VI: Chỉ bắt buộc khi COMPLETE session chưa gắn knowledge_node (Topic để lưu).
  topic_id?: string
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