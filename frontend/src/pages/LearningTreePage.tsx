/**
 * pages/LearningTreePage.tsx
 *
 * JA: 学習内容の検索木構造画面。組み立てのみ行い、中身は features/learningTree に置く。
 *     ★「木構造」/「タイムログ」をボタンで切り替えられるようにする。木構造は
 *     知識ノード化されたものしか出ないため、途中まで学習した内容も含めて時系列で
 *     振り返れるタイムログ(ChatTimelineView)を同じ画面に用意する。
 *     ★「今日の復習」一覧(DueReviewList)はどちらのビューでも上に固定表示する。
 *     木を自分で開いて葉を探さなくても、放置が長い順に復習に入れるようにするため
 *     (実用化監査 P1-1)。
 * VI: Trang cây nội dung đã học (có tìm kiếm). Chỉ lắp ghép, nội dung nằm ở features/learningTree.
 *     ★Cho phép bấm nút chuyển "Cây" / "Nhật ký thời gian". Cây chỉ hiện phần đã thành
 *     knowledge node, nên chuẩn bị thêm Nhật ký thời gian (ChatTimelineView) ngay trong
 *     cùng màn hình để xem lại cả phần học dở theo thứ tự thời gian.
 *     ★Danh sách "Ôn tập hôm nay" (DueReviewList) luôn hiện cố định phía trên, ở cả 2 view.
 *     Để không cần tự mở cây tìm lá, vào ôn theo thứ tự bỏ quên lâu nhất
 *     (audit thực dụng hóa P1-1).
 */
import { useState } from 'react'

import { Link } from 'react-router-dom'

import { ChatTimelineView } from '@/features/learningTree/components/ChatTimelineView'
import { LearningTreeView } from '@/features/learningTree/components/LearningTreeView'
import { DueReviewList } from '@/features/reviews/components/DueReviewList'

type ViewMode = 'tree' | 'timeline'

export function LearningTreePage() {
  const [viewMode, setViewMode] = useState<ViewMode>('tree')

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

      <DueReviewList />

      <div className="inline-flex rounded-2xl border border-slate-200 bg-white p-1 shadow-sm">
        <button
          type="button"
          onClick={() => setViewMode('tree')}
          className={`rounded-xl px-4 py-1.5 text-sm font-medium transition-colors ${
            viewMode === 'tree' ? 'bg-teal-600 text-white' : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          木構造 / Cây
        </button>
        <button
          type="button"
          onClick={() => setViewMode('timeline')}
          className={`rounded-xl px-4 py-1.5 text-sm font-medium transition-colors ${
            viewMode === 'timeline' ? 'bg-teal-600 text-white' : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          タイムログ / Nhật ký thời gian
        </button>
      </div>

      {viewMode === 'tree' ? <LearningTreeView /> : <ChatTimelineView />}
    </main>
  )
}
