/**
 * features/reviews/api/hooks.ts
 *
 * JA: 復習スケジュールのサーバ状態を扱う TanStack Query フック。通信は必ず shared/api の api 経由。
 *     このfeatureは基本的に「学習木の葉をどう塗るか」の材料(mastery_level・is_due)を
 *     提供するだけで、復習チャットそのもの(いつ・どう復習するか)には踏み込まない。
 *     ★ただし「今日の復習」一覧からワンクリックで復習に入れないと一覧の意味が無いため、
 *     start-review だけは例外的にここに持つ(features/learningTree にも同じ形のフックが
 *     あるが、features 同士は直接importしない規約(CONVENTIONS.md §2)のため再定義)。
 * VI: Hook TanStack Query xử lý trạng thái server của lịch ôn tập. Giao tiếp luôn qua api của shared/api.
 *     Feature này về cơ bản chỉ cung cấp nguyên liệu (mastery_level, is_due) để tô lá cây học tập,
 *     không động vào bản thân việc ôn tập qua chat (khi nào/ôn thế nào).
 *     ★Nhưng nếu danh sách "Ôn tập hôm nay" không cho vào ôn ngay bằng 1 click thì mất ý nghĩa,
 *     nên start-review là ngoại lệ được đặt ở đây (features/learningTree cũng có hook dạng này
 *     nhưng quy ước không import chéo giữa features (CONVENTIONS.md §2) nên định nghĩa lại).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { ChatSession, ReviewSchedule } from '@/shared/types'

export function useReviewSchedules() {
  return useQuery({
    queryKey: queryKeys.reviews.schedules(),
    queryFn: () => api.get<ReviewSchedule[]>('/review-schedules/'),
  })
}

// JA: 復習予定日を過ぎた葉だけを、放置が長い順(古いnext_review_atから)で取得する。
//     「今日の復習」一覧の材料。並び順はバックエンド(ReviewScheduleViewSet.due)が保証する。
// VI: Lấy các lá đã quá hạn ôn, sắp theo thứ tự bỏ quên lâu nhất (next_review_at cũ nhất trước).
//     Nguyên liệu cho danh sách "Ôn tập hôm nay". Thứ tự do backend (ReviewScheduleViewSet.due) đảm bảo.
export function useDueReviews() {
  return useQuery({
    queryKey: queryKeys.reviews.due(),
    queryFn: () => api.get<ReviewSchedule[]>('/review-schedules/due/'),
  })
}

// JA: 葉(知識ノード)に対応するチャットセッションを get-or-create する。
//     詳細は features/learningTree/api/hooks.ts の同名フックのコメント参照。
// VI: get-or-create phiên chat tương ứng với lá (knowledge node).
//     Chi tiết xem comment ở hook cùng tên trong features/learningTree/api/hooks.ts.
export function useStartReviewSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (nodeId: string) =>
      api.post<ChatSession>('/chat-sessions/', { node_id: nodeId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.all })
    },
  })
}
