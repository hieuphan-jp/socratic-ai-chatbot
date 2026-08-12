/**
 * features/learningTree/api/mockData.ts
 *
 * JA: 学習内容ツリーのモックデータ。バックエンドAPIが未実装のため、ここでは
 *     ダミーの木構造を返すだけ。呼び出し元は `api/hooks.ts` の `useLearningTree()`。
 *     `services.py` が用意でき次第 hooks.ts 側の queryFn を差し替え、本ファイルは削除する。
 * VI: Dữ liệu giả cho cây nội dung đã học. Do backend API chưa có, ở đây chỉ trả về
 *     cây dữ liệu giả. Nơi gọi là `useLearningTree()` trong `api/hooks.ts`.
 *     Khi `services.py` sẵn sàng, thay queryFn ở hooks.ts và xóa file này.
 */

import type { TreeNode } from '@/shared/types'

const MOCK_TREE: TreeNode[] = [
  {
    id: 'math',
    label: '数学 / Toán học',
    children: [
      {
        id: 'math-algebra',
        label: '代数 / Đại số',
        children: [
          { id: 'math-algebra-linear', label: '一次方程式 / Phương trình bậc nhất' },
          { id: 'math-algebra-quadratic', label: '二次方程式 / Phương trình bậc hai' },
        ],
      },
      {
        id: 'math-geometry',
        label: '幾何 / Hình học',
        children: [{ id: 'math-geometry-triangle', label: '三角形 / Tam giác' }],
      },
    ],
  },
  {
    id: 'programming',
    label: 'プログラミング / Lập trình',
    children: [
      {
        id: 'programming-python',
        label: 'Python',
        children: [
          { id: 'programming-python-basic', label: '基本文法 / Cú pháp cơ bản' },
          { id: 'programming-python-oop', label: 'オブジェクト指向 / Hướng đối tượng' },
        ],
      },
      {
        id: 'programming-web',
        label: 'Web',
        children: [{ id: 'programming-web-react', label: 'React' }],
      },
    ],
  },
]

// JA: 一覧取得のモック関数。実API化までの繋ぎ。
// VI: Hàm giả lập lấy danh sách. Dùng tạm cho tới khi có API thật.
export function fetchMockLearningTree(): TreeNode[] {
  return MOCK_TREE
}
