/**
 * features/learningTree/api/hooks.ts
 *
 * JA: 学習内容ツリーのサーバ状態を扱う TanStack Query フック。通信は必ず shared/api の api 経由。
 * VI: Hook TanStack Query xử lý trạng thái server của cây nội dung đã học. Giao tiếp luôn qua api của shared/api.
 */
import { useQuery } from '@tanstack/react-query'

import { api } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { TreeNode } from '@/shared/types'

export function useLearningTree() {
  return useQuery({
    queryKey: queryKeys.learningTree.list(),
    queryFn: () => api.get<TreeNode[]>('/learning-tree/'),
  })
}
