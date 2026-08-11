/**
 * pages/LearningTreePage.tsx
 *
 * JA: 学習内容の検索木構造画面。組み立てのみ行い、中身は features/learningTree に置く。
 * VI: Trang cây nội dung đã học (có tìm kiếm). Chỉ lắp ghép, nội dung nằm ở features/learningTree.
 */
import { Link } from 'react-router-dom'

import { LearningTreeView } from '@/features/learningTree/components/LearningTreeView'

export function LearningTreePage() {
  return (
    <main style={{ maxWidth: 560, margin: '40px auto', display: 'grid', gap: 20 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 20 }}>学習内容ツリー / Cây nội dung đã học</h1>
        <Link to="/">戻る / Quay lại</Link>
      </header>
      <LearningTreeView />
    </main>
  )
}
