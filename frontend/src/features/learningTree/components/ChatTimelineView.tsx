/**
 * features/learningTree/components/ChatTimelineView.tsx
 *
 * JA: 学習内容ツリー画面の「タイムログ」表示。Gemini等の左サイドバーのように、
 *     ユーザーの全チャットセッションを作成日時の新しい順に一覧表示し、選ぶと
 *     そのセッションの時系列ダイアログ(ChatHistoryPanel)を読み返せる。
 *     ★知識ノード化(完了ボタン)されているかは問わない。学習内容ツリー(木構造)は
 *     知識ノード化されたものしか出ないため、「途中まで学習した内容も振り返りたい」
 *     という用途はこちらが担う。LearningTreePage側でボタン切替してこの画面を出す。
 *     ★選んだセッションには「復習を始める」/「学習を再開する」ボタンを出し、実際に
 *     そのチャット画面(/hint-chat/:sessionId)に入って続きを対話できるようにする。
 *     ここでは既にセッションID自体がタイムログの一覧に載っているため、
 *     NodeDetailPanelのようなget-or-create(node_id→session_id)は不要で、
 *     素直にそのIDへ遷移するだけでよい。
 * VI: View "Nhật ký thời gian" của màn hình cây nội dung đã học. Giống sidebar bên
 *     trái của Gemini, liệt kê toàn bộ phiên chat của user theo thời gian tạo mới
 *     nhất trước, chọn vào để đọc lại hội thoại (ChatHistoryPanel) theo thứ tự thời gian.
 *     ★Không phân biệt đã tạo knowledge node (đã hoàn thành) hay chưa. Cây nội dung đã
 *     học chỉ hiện phần đã thành knowledge node, nên nhu cầu "xem lại cả phần học dở"
 *     do view này đảm nhiệm. LearningTreePage bấm nút để chuyển sang view này.
 *     ★Session đang chọn có nút "Bắt đầu ôn tập" / "Tiếp tục học" để vào thẳng màn
 *     hình chat (/hint-chat/:sessionId) và nói tiếp. Ở đây ID session đã có sẵn trong
 *     danh sách nhật ký thời gian nên không cần get-or-create (node_id→session_id)
 *     như NodeDetailPanel, chỉ cần điều hướng thẳng tới ID đó.
 */
import { useState } from 'react'

import { MessageCircle, MessagesSquare, Play } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { LOCALE_TO_INTL, useI18n } from '@/shared/i18n'
import { ErrorText } from '@/shared/ui'

import { useAllChatSessions } from '../api/hooks'
import { ChatHistoryPanel } from './ChatHistoryPanel'

function formatSessionDate(
  isoString: string,
  intlLocale: string,
  t: (key: 'learningTree.timeline.today' | 'learningTree.timeline.yesterday', params: { time: string }) => string
): string {
  const date = new Date(isoString)
  const now = new Date()
  const isSameDay = date.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  const isYesterday = date.toDateString() === yesterday.toDateString()

  const time = date.toLocaleTimeString(intlLocale, { hour: '2-digit', minute: '2-digit' })
  if (isSameDay) return t('learningTree.timeline.today', { time })
  if (isYesterday) return t('learningTree.timeline.yesterday', { time })
  return `${date.toLocaleDateString(intlLocale, { month: 'short', day: 'numeric' })} ${time}`
}

export function ChatTimelineView() {
  const { t, locale } = useI18n()
  const { data: sessions, isPending, isError, error } = useAllChatSessions()
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const navigate = useNavigate()

  if (isPending) return <p className="text-sm text-slate-400">{t('common.loading')}</p>
  if (isError) return <ErrorText>{(error as Error).message}</ErrorText>

  const selectedSession = sessions.find((s) => String(s.id) === selectedSessionId)
  const intlLocale = LOCALE_TO_INTL[locale]

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
      <div className="space-y-1 rounded-3xl border border-slate-100 bg-white p-4 shadow-sm">
        {sessions.length === 0 ? (
          <p className="px-2 py-6 text-center text-sm text-slate-400">
            {t('learningTree.timeline.empty')}
          </p>
        ) : (
          sessions.map((session) => {
            const isSelected = String(session.id) === selectedSessionId
            return (
              <button
                key={session.id}
                type="button"
                onClick={() => setSelectedSessionId(String(session.id))}
                className={`flex w-full items-start gap-2 rounded-xl px-3 py-2 text-left text-sm transition-colors ${
                  isSelected ? 'bg-teal-50 text-teal-800' : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                <MessageCircle
                  className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${isSelected ? 'text-teal-600' : 'text-slate-400'}`}
                />
                <div className="min-w-0">
                  <p className="truncate font-medium">{session.title}</p>
                  <p className={`text-[11px] ${isSelected ? 'text-teal-600' : 'text-slate-400'}`}>
                    {formatSessionDate(session.created_at, intlLocale, t)}
                  </p>
                </div>
              </button>
            )
          })
        )}
      </div>

      <div className="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        {selectedSession ? (
          <>
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="min-w-0 truncate text-sm font-semibold text-slate-800">
                {selectedSession.title}
              </h3>
              <button
                type="button"
                onClick={() => navigate(`/hint-chat/${selectedSession.id}`)}
                // ★teal-700。白文字コントラストがWCAG AA未達(3.66:1)だったteal-600から変更(Button.tsx参照)。
                className="flex shrink-0 items-center gap-1.5 rounded-2xl bg-teal-700 px-3.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-teal-800"
              >
                <Play className="h-3 w-3" />
                {selectedSession.knowledge_node
                  ? t('learningTree.review.start')
                  : t('learningTree.review.resume')}
              </button>
            </div>
            <ChatHistoryPanel sessionId={String(selectedSession.id)} />
          </>
        ) : (
          <div className="flex h-full min-h-[240px] flex-col items-center justify-center gap-2 text-slate-300">
            <MessagesSquare className="h-8 w-8" />
            <p className="text-sm text-slate-400">{t('learningTree.timeline.selectPrompt')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
