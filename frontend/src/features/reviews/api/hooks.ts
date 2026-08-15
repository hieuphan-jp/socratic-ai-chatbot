/**
 * features/reviews/api/hooks.ts
 *
 * JA: 復習スケジュールのサーバ状態を扱う TanStack Query フック。通信は必ず shared/api の api 経由。
 *     このfeatureは「学習木の葉をどう塗るか」の材料(mastery_level・is_due)を提供するだけで、
 *     復習チャットそのもの(いつ・どう復習するか)には踏み込まない。
 * VI: Hook TanStack Query xử lý trạng thái server của lịch ôn tập. Giao tiếp luôn qua api của shared/api.
 *     Feature này chỉ cung cấp nguyên liệu (mastery_level, is_due) để tô lá cây học tập,
 *     không động vào bản thân việc ôn tập qua chat (khi nào/ôn thế nào).
 */
import { useQuery } from '@tanstack/react-query'

import { api } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { ReviewSchedule } from '@/shared/types'

export function useReviewSchedules() {
  return useQuery({
    queryKey: queryKeys.reviews.schedules(),
    queryFn: () => api.get<ReviewSchedule[]>('/review-schedules/'),
  })
}
