/**
 * features/learningTree/api/hooks.ts
 *
 * JA: 学習内容ツリーのサーバ状態を扱う TanStack Query フック。通信は必ず shared/api の api 経由。
 * VI: Hook TanStack Query xử lý trạng thái server của cây nội dung đã học. Giao tiếp luôn qua api của shared/api.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { ChatMessage, ChatSession, KnowledgeNodeDetail, TreeNode } from '@/shared/types'

export function useLearningTree() {
  return useQuery({
    queryKey: queryKeys.learningTree.list(),
    queryFn: () => api.get<TreeNode[]>('/learning-tree/'),
  })
}

// JA: 葉(知識ノード)をクリックした時に、本文を含む詳細を取得する。
//     nodeId が空の間は叩かない(何も選ばれていない状態)。
// VI: Lấy chi tiết (kèm nội dung) khi bấm vào lá (knowledge node).
//     Không gọi khi nodeId rỗng (chưa chọn gì).
export function useKnowledgeNodeDetail(nodeId: string | null) {
  return useQuery({
    queryKey: queryKeys.learningTree.node(nodeId ?? ''),
    queryFn: () => api.get<KnowledgeNodeDetail>(`/knowledge-nodes/${nodeId}/`),
    enabled: !!nodeId,
  })
}

// JA: 葉(知識ノード)に紐づくチャットセッションの、時系列順の会話ログを取得する。
//     sessionId は ReviewSchedule.chat_session_id から渡す(「過去のチャットに
//     戻るための行き先」、apps/reviews/serializers.py 参照)。木構造(思考ツリー)
//     ではなく時系列の一覧が欲しいので /messages/ を叩く(/graph/ ではない)。
// VI: Lấy log hội thoại theo thứ tự thời gian của phiên chat gắn với lá
//     (knowledge node). sessionId truyền từ ReviewSchedule.chat_session_id
//     (xem apps/reviews/serializers.py). Gọi /messages/ (không phải /graph/)
//     vì cần danh sách theo thời gian, không phải cây tư duy.
export function useChatSessionMessages(sessionId: string | null) {
  return useQuery({
    queryKey: queryKeys.chat.messages(sessionId ?? ''),
    queryFn: () => api.get<ChatMessage[]>(`/chat-sessions/${sessionId}/messages/`),
    enabled: !!sessionId,
  })
}

// JA: タイムログ表示用に、ユーザーの全チャットセッションを新しい順で取得する。
//     ★知識ノード化(完了ボタン)されたかどうかは問わない。学習内容ツリーは
//     知識ノード化されたものしか出ないため、「途中まで学習した内容も含めて
//     振り返りたい」用途はこちら(GET /chat-sessions/、-created_atソート済み)で満たす。
//     features/hintChat にも同じ形のフックがあるが、features 同士は直接importしない
//     規約(CONVENTIONS.md §2)のためここに再定義している。
// VI: Lấy toàn bộ phiên chat của user, mới nhất trước, dùng cho view Nhật ký thời gian.
//     ★Không phân biệt đã tạo knowledge node (đã hoàn thành) hay chưa. Cây nội dung đã học
//     chỉ hiện phần đã thành knowledge node, nên nhu cầu "xem lại cả phần học dở" được đáp
//     ứng ở đây (GET /chat-sessions/, đã sort theo -created_at).
//     features/hintChat cũng có hook dạng này nhưng quy ước không import chéo giữa các
//     features (CONVENTIONS.md §2) nên định nghĩa lại ở đây.
export function useAllChatSessions() {
  return useQuery({
    queryKey: queryKeys.chat.all,
    queryFn: () => api.get<ChatSession[]>('/chat-sessions/'),
  })
}

// JA: ★葉(知識ノード)から復習チャットを開くための入口。POST /chat-sessions/ に node_id を
//     渡すと、バックエンドの create_chat_session_for_node が
//     「そのノードに既にセッションがあれば それを返し、無ければ作る」(get-or-create)ため、
//     呼び出し側は既存/新規を気にしなくてよい。
//     ★chat_session_id が既に分かっている場合でもこの経路を通す。手動作成やseedで
//     作られたノードにはセッションが無く(chat_session_id=null)、そこを分岐すると
//     「復習を始められない葉」が生まれてしまうため、常に同じ1本の経路にする。
//     所有権チェックは窓口関数 get_owned_knowledge_node が行う(CONVENTIONS.md §10)。
// VI: ★Lối vào chat ôn tập từ lá (knowledge node). Truyền node_id vào POST /chat-sessions/
//     thì create_chat_session_for_node ở backend sẽ "trả về phiên đã có của node đó, chưa có
//     thì tạo mới" (get-or-create), nên bên gọi không cần phân biệt cũ/mới.
//     ★Kể cả khi đã biết chat_session_id vẫn đi qua đường này. Node tạo tay hoặc do seed
//     chưa có phiên (chat_session_id=null); nếu rẽ nhánh theo giá trị đó sẽ sinh ra những
//     lá "không ôn tập được", nên luôn dùng chung một đường.
//     Việc kiểm tra quyền sở hữu do hàm cửa ngõ get_owned_knowledge_node đảm nhiệm (§10).
export function useStartReviewSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (nodeId: string) =>
      api.post<ChatSession>('/chat-sessions/', { node_id: nodeId }),
    onSuccess: () => {
      // JA: 新規に作られた場合はタイムログの一覧に増えるので取り直す。
      // VI: Nếu vừa tạo mới thì danh sách nhật ký thời gian có thêm mục, nên lấy lại.
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.all })
    },
  })
}
