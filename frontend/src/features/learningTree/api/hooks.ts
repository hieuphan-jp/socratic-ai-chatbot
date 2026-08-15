/**
 * features/learningTree/api/hooks.ts
 *
 * JA: 学習内容ツリーのサーバ状態を扱う TanStack Query フック。通信は必ず shared/api の api 経由。
 * VI: Hook TanStack Query xử lý trạng thái server của cây nội dung đã học. Giao tiếp luôn qua api của shared/api.
 */
import { useQuery } from '@tanstack/react-query'

import { api } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { KnowledgeNodeDetail, TreeNode } from '@/shared/types'

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
