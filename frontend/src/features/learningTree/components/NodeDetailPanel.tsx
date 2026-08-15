/**
 * features/learningTree/components/NodeDetailPanel.tsx
 *
 * JA: 選択中の葉(知識ノード)の詳細(本文・定着度・次回復習日)を表示する。
 *     復習チャットへの導線(過去セッションに入り直す等)はチャット機能側との
 *     統合作業でつなぐ予定のため、ここでは持たない(範囲外)。
 * VI: Hiển thị chi tiết (nội dung, độ ghi nhớ, ngày ôn kế tiếp) của lá đang chọn.
 *     Lối vào chat ôn tập (mở lại session cũ...) sẽ nối ở giai đoạn tích hợp với
 *     tính năng Chat, nên chưa có ở đây (ngoài phạm vi lần này).
 */
import { BookOpen, Calendar, Clock, X } from 'lucide-react'

import { ErrorText } from '@/shared/ui'
import type { ReviewSchedule } from '@/shared/types'

import { useKnowledgeNodeDetail } from '../api/hooks'

interface NodeDetailPanelProps {
  nodeId: string
  schedule: ReviewSchedule | undefined
  onClose: () => void
}

export function NodeDetailPanel({ nodeId, schedule, onClose }: NodeDetailPanelProps) {
  const { data, isPending, isError, error } = useKnowledgeNodeDetail(nodeId)

  return (
    <div className="flex h-full flex-col rounded-3xl border border-slate-100 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div className="flex items-center gap-2 text-slate-700">
          <BookOpen className="h-4 w-4 text-teal-600" />
          <h3 className="text-sm font-semibold">ノードの詳細 / Chi tiết node</h3>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1 text-slate-400 hover:bg-slate-50 hover:text-slate-600"
          aria-label="閉じる / Đóng"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {isPending && <p className="text-sm text-slate-400">読み込み中… / Đang tải…</p>}
        {isError && <ErrorText>{(error as Error).message}</ErrorText>}

        {data && (
          <>
            <div>
              <p className="text-[11px] text-slate-400">{data.topic_name}</p>
              <h4 className="mt-0.5 text-base font-semibold text-slate-800">{data.title}</h4>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-600">
              {data.content}
            </p>

            <div className="space-y-2 rounded-2xl border border-slate-100 bg-slate-50/70 p-3 text-xs text-slate-500">
              {schedule ? (
                <>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>
                      定着度 / Độ ghi nhớ: {schedule.mastery_level} / {schedule.mastery_max_level}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5" />
                    <span>
                      {schedule.is_due
                        ? `復習の時期です(${schedule.days_overdue}日超過) / Đã tới hạn ôn (quá ${schedule.days_overdue} ngày)`
                        : `次回復習予定 / Lần ôn kế tiếp: ${new Date(schedule.next_review_at).toLocaleDateString('ja-JP')}`}
                    </span>
                  </div>
                </>
              ) : (
                <p>未学習(まだ復習記録がありません) / Chưa học (chưa có bản ghi ôn tập)</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
