/**
 * features/learningTree/components/NodeDetailPanel.tsx
 *
 * JA: 選択中の葉(知識ノード)の詳細(本文・定着度・次回復習日)を表示する。
 *     ★「詳細」/「会話ログ」のタブ切替で、この葉を生んだチャットセッションの
 *     時系列ダイアログ(発言順そのまま、思考ツリーの枝分かれ形ではない)も
 *     同じ画面内で見られるようにする。行き先は ReviewSchedule.chat_session_id
 *     (apps/reviews/serializers.py 参照、「その葉から過去のチャットに戻るための
 *     行き先」として既に用意されている)。手動作成などでチャットセッションが
 *     無い葉では会話ログタブ自体を出さない。
 *     ★さらに「復習を始める」で、その葉のチャットセッションに実際に入り直せる
 *     (会話ログタブは読むだけなので、続きを対話するにはチャット画面へ移る必要がある)。
 *     これが要件のパターン2「対応する過去のチャットセッションに再度入る」に当たる。
 * VI: Hiển thị chi tiết (nội dung, độ ghi nhớ, ngày ôn kế tiếp) của lá đang chọn.
 *     ★Chuyển tab "Chi tiết" / "Lịch sử hội thoại" để xem cả hội thoại theo thứ
 *     tự thời gian (đúng thứ tự phát ngôn, không phải dạng rẽ nhánh của cây tư
 *     duy) của phiên chat đã sinh ra lá này, ngay trong cùng màn hình. Điểm đến
 *     lấy từ ReviewSchedule.chat_session_id (xem apps/reviews/serializers.py,
 *     đã có sẵn với vai trò "đích để quay lại cuộc trò chuyện cũ từ lá đó"). Lá
 *     không có phiên chat (vd tạo tay) thì không hiện tab lịch sử hội thoại.
 *     ★Ngoài ra nút "Bắt đầu ôn tập" cho phép vào lại đúng phiên chat của lá đó
 *     (tab lịch sử chỉ để đọc, muốn nói tiếp thì phải sang màn hình chat).
 *     Đây chính là bước "vào lại phiên chat cũ tương ứng" ở pattern 2 của yêu cầu.
 */
import { useState } from 'react'

import { useNavigate } from 'react-router-dom'

import { BookOpen, Calendar, Clock, MessageSquare, Play, X } from 'lucide-react'

import { LOCALE_TO_INTL, useI18n } from '@/shared/i18n'
import { ErrorText } from '@/shared/ui'
import type { ReviewSchedule } from '@/shared/types'

import { useKnowledgeNodeDetail, useStartReviewSession } from '../api/hooks'
import { ChatHistoryPanel } from './ChatHistoryPanel'

interface NodeDetailPanelProps {
  nodeId: string
  schedule: ReviewSchedule | undefined
  onClose: () => void
}

type Tab = 'detail' | 'chatHistory'

export function NodeDetailPanel({ nodeId, schedule, onClose }: NodeDetailPanelProps) {
  const { t, locale } = useI18n()
  const { data, isPending, isError, error } = useKnowledgeNodeDetail(nodeId)
  const [tab, setTab] = useState<Tab>('detail')
  const chatSessionId = schedule?.chat_session_id ?? null
  const navigate = useNavigate()
  const startReview = useStartReviewSession()

  // JA: 葉に対応するチャットセッションを get-or-create してから、その画面へ移る。
  //     セッションIDが既知でも同じ経路を通す(理由は useStartReviewSession のコメント)。
  // VI: get-or-create phiên chat của lá rồi chuyển sang màn hình đó.
  //     Kể cả khi đã biết ID vẫn đi chung đường (lý do xem comment ở useStartReviewSession).
  const handleStartReview = () => {
    startReview.mutate(nodeId, {
      onSuccess: (session) => navigate(`/hint-chat/${session.id}`),
    })
  }

  return (
    <div className="flex h-full flex-col rounded-3xl border border-slate-100 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div className="flex items-center gap-2 text-slate-700">
          <BookOpen className="h-4 w-4 text-teal-600" />
          <h3 className="text-sm font-semibold">{t('learningTree.node.detail')}</h3>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border-0 bg-transparent p-1 text-slate-400 hover:bg-slate-50 hover:text-slate-600"
          aria-label={t('common.close')}
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {chatSessionId && (
        <div className="flex gap-1 border-b border-slate-100 px-5 pt-3">
          <button
            type="button"
            onClick={() => setTab('detail')}
            className={`rounded-t-lg border-x-0 border-t-0 border-b-2 bg-transparent px-3 py-1.5 text-xs font-medium ${
              tab === 'detail'
                ? 'border-teal-600 text-teal-700'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            {t('learningTree.node.tab.detail')}
          </button>
          <button
            type="button"
            onClick={() => setTab('chatHistory')}
            className={`flex items-center gap-1 rounded-t-lg border-x-0 border-t-0 border-b-2 bg-transparent px-3 py-1.5 text-xs font-medium ${
              tab === 'chatHistory'
                ? 'border-teal-600 text-teal-700'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            <MessageSquare className="h-3 w-3" />
            {t('learningTree.node.tab.chatHistory')}
          </button>
        </div>
      )}

      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {tab === 'chatHistory' && chatSessionId ? (
          <ChatHistoryPanel sessionId={chatSessionId} />
        ) : (
          <>
            {isPending && <p className="text-sm text-slate-400">{t('common.loading')}</p>}
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
                          {t('learningTree.node.masteryLabel', {
                            level: schedule.mastery_level,
                            max: schedule.mastery_max_level,
                          })}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5" />
                        <span>
                          {schedule.is_due
                            ? t('learningTree.node.dueOverdue', { days: schedule.days_overdue })
                            : t('learningTree.node.nextReview', {
                                date: new Date(schedule.next_review_at).toLocaleDateString(
                                  LOCALE_TO_INTL[locale]
                                ),
                              })}
                        </span>
                      </div>
                    </>
                  ) : (
                    <p>{t('learningTree.node.unlearned')}</p>
                  )}
                </div>
              </>
            )}
          </>
        )}
      </div>

      {/* JA: ★復習フローの入口。どちらのタブを見ていても押せるようフッターに固定する。
              VI: ★Lối vào luồng ôn tập. Đặt cố định ở footer để tab nào cũng bấm được. */}
      <div className="border-t border-slate-100 px-5 py-4">
        <button
          type="button"
          onClick={handleStartReview}
          disabled={startReview.isPending}
          // ★teal-700。白文字コントラストがWCAG AA未達(3.66:1)だったteal-600から変更(Button.tsx参照)。
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-teal-700 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          <Play className="h-3.5 w-3.5" />
          {startReview.isPending
            ? t('learningTree.review.opening')
            : chatSessionId
              ? t('learningTree.review.start')
              : t('learningTree.review.startFromChat')}
        </button>
        {startReview.isError && (
          <div className="mt-2">
            <ErrorText>{(startReview.error as Error).message}</ErrorText>
          </div>
        )}
      </div>
    </div>
  )
}
