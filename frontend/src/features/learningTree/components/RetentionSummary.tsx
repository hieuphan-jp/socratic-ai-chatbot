/**
 * features/learningTree/components/RetentionSummary.tsx
 *
 * JA: 木全体の定着率(%)を表示する。ユーザーがこの数字を100%緑に近づけることを
 *     目標に復習するためのモチベーション表示(要件定義より)。
 * VI: Hiển thị tỉ lệ ghi nhớ (%) của cả cây. Là chỉ số tạo động lực để user ôn tập
 *     cho tới khi cây gần như 100% xanh (theo yêu cầu thiết kế).
 */
import { Leaf } from 'lucide-react'

interface RetentionSummaryProps {
  percent: number
  notDue: number
  total: number
}

export function RetentionSummary({ percent, notDue, total }: RetentionSummaryProps) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-emerald-100 bg-emerald-50/60 px-5 py-4">
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600">
        <Leaf className="h-6 w-6" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-emerald-700">
            {total === 0 ? '—' : `${percent}%`}
          </span>
          <span className="text-xs text-slate-500">
            定着中のノード / Node đã ghi nhớ ({notDue}/{total})
          </span>
        </div>
        <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-emerald-100/80">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all"
            style={{ width: `${total === 0 ? 0 : percent}%` }}
          />
        </div>
      </div>
    </div>
  )
}
