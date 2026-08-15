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
    <main className="mx-auto max-w-4xl space-y-6 p-4 sm:p-6">
      <div className="flex items-center justify-between rounded-3xl border border-slate-100 bg-gradient-to-r from-teal-50/60 via-indigo-50/40 to-slate-50 p-6">
        <div>
          <h1 className="text-lg font-semibold text-slate-800">学習内容ツリー</h1>
          <p className="mt-0.5 text-xs text-slate-500">Cây nội dung đã học</p>
        </div>
        <Link to="/" className="text-sm text-indigo-600 hover:underline">
          戻る / Quay lại
        </Link>
      </div>
      <LearningTreeView />
    </main>
  )
}
