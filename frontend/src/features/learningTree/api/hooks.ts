/**
 * features/learningTree/api/hooks.ts
 *
 * JA: 学習内容ツリーのサーバ状態を扱う TanStack Query フック。通信は必ず shared/api の api 経由。
 *     現在はバックエンドAPI未実装のため queryFn はモック関数を呼ぶ。実装完了後は
 *     `api.get<TreeNode[]>('/learning-tree/')` に1行差し替える。
 * VI: Hook TanStack Query xử lý trạng thái server của cây nội dung đã học. Giao tiếp luôn qua api của shared/api.
 *     Hiện backend API chưa có nên queryFn gọi hàm mock. Sau khi có API thật, thay 1 dòng
 *     bằng `api.get<TreeNode[]>('/learning-tree/')`.
 */
import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/api/queryKeys'
import type { TreeNode } from '@/shared/types'

import { fetchMockLearningTree } from './mockData'

export function useLearningTree() {
  return useQuery({
    queryKey: queryKeys.learningTree.list(),
    // TODO: バックエンド完成後、下の1行に差し替える / Sau khi có backend, thay bằng dòng dưới
    // queryFn: () => api.get<TreeNode[]>('/learning-tree/'),
    queryFn: (): Promise<TreeNode[]> => Promise.resolve(fetchMockLearningTree()),
  })
}
