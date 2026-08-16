/**
 * features/reviews/components/DueReviewList.tsx
 *
 * JA: 「今日の復習」一覧。ワークフロー定義のパターン2 step 1-2
 *     (「木構造の中で、エビングハウスの忘却曲線に基づいた計算とATTEMPTの最新の
 *     復習タイミングに基づき、各KNOWLEDGE_NODEの色が変換」→ユーザーがそれを見て
 *     選ぶ)を、木を自分で開いて回らなくても済むように一覧化したもの。
 *     GET /review-schedules/due/ はバックエンドで実装済みだったが、フロントから
 *     一度も呼ばれておらず、ノードが増えると「今日やるべきこと」に辿り着けない
 *     状態だった(実用化監査の指摘 P1-1)。クリックすると即座に復習チャットへ入る。
 * VI: Danh sách "Ôn tập hôm nay". Gom hóa bước 1-2 của pattern 2 trong workflow
 *     (cây tô màu theo đường cong quên Ebbinghaus + thời điểm ôn gần nhất của
 *     Attempt → user nhìn màu mà chọn) thành 1 danh sách, để không phải tự mở
 *     cây đi tìm. GET /review-schedules/due/ đã có sẵn ở backend nhưng frontend
 *     chưa từng gọi, khi số node tăng lên thì không biết "hôm nay phải ôn cái gì"
 *     (audit thực dụng hóa chỉ ra ở P1-1). Bấm vào là vào thẳng chat ôn tập.
 */
import { CheckCircle2, Clock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { ErrorText } from '@/shared/ui'

import { useDueReviews, useStartReviewSession } from '../api/hooks'

export function DueReviewList() {
  const { data, isPending, isError, error } = useDueReviews()
  const startReview = useStartReviewSession()
  const navigate = useNavigate()

  const handleStart = (nodeId: string) => {
    startReview.mutate(nodeId, {
      onSuccess: (session) => navigate(`/hint-chat/${session.id}`),
    })
  }

  if (isPending) return <p className="text-sm text-slate-400">読み込み中… / Đang tải…</p>
  if (isError) return <ErrorText>{(error as Error).message}</ErrorText>

  return (
    <div className="rounded-3xl border border-amber-100 bg-amber-50/50 p-5">
      <div className="mb-3 flex items-center gap-2">
        <Clock className="h-4 w-4 text-amber-600" />
        <h2 className="text-sm font-semibold text-slate-800">今日の復習</h2>
        <span className="text-xs text-slate-500">/ Ôn tập hôm nay</span>
        {data.length > 0 && (
          <span className="ml-auto rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
            {data.length}
          </span>
        )}
      </div>

      {data.length === 0 ? (
        <div className="flex items-center gap-2 rounded-2xl bg-white/70 px-4 py-3 text-sm text-emerald-700">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          復習が必要なノードはありません / Không có node nào cần ôn tập
        </div>
      ) : (
        <div className="space-y-1.5">
          {data.map((schedule) => (
            <button
              key={schedule.id}
              type="button"
              onClick={() => handleStart(schedule.node_id)}
              disabled={startReview.isPending}
              className="flex w-full items-center justify-between gap-3 rounded-2xl bg-white px-4 py-2.5 text-left text-sm shadow-sm transition-colors hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span className="min-w-0 truncate font-medium text-slate-700">
                {schedule.node_title}
              </span>
              <span className="shrink-0 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-700">
                {schedule.days_overdue > 0
                  ? `${schedule.days_overdue}日超過 / quá ${schedule.days_overdue} ngày`
                  : '本日 / hôm nay'}
              </span>
            </button>
          ))}
        </div>
      )}

      {startReview.isError && (
        <div className="mt-2">
          <ErrorText>{(startReview.error as Error).message}</ErrorText>
        </div>
      )}
    </div>
  )
}
