/**
 * features/learningTree/components/ChatHistoryPanel.tsx
 *
 * JA: 学習内容ツリーの葉から開く、過去チャットの時系列ダイアログ表示。
 *     features/hintChat には「思考ツリー(枝分かれ)」の表示があるが、ここは
 *     ツリー画面の一部として「発言順そのまま」を読み返したいだけなので、
 *     GET /chat-sessions/{id}/messages/ の並び(created_at昇順)をそのまま出す
 *     軽量な読み取り専用ビューにする(features 同士は直接 import しないため、
 *     hintChat の部品は再利用せずここに最小限だけ書く)。
 * VI: Hiển thị hội thoại quá khứ theo thứ tự thời gian, mở từ lá của cây nội
 *     dung đã học. features/hintChat có sẵn view "cây tư duy" (rẽ nhánh), nhưng
 *     ở đây chỉ cần đọc lại đúng thứ tự phát ngôn trong màn hình cây, nên hiển
 *     thị thẳng theo thứ tự GET /chat-sessions/{id}/messages/ (created_at tăng
 *     dần) dạng view chỉ đọc, tối giản (không import chéo feature nên không
 *     dùng lại component của hintChat).
 */
import { ErrorText, Notice } from '@/shared/ui'

import { useChatSessionMessages } from '../api/hooks'

interface ChatHistoryPanelProps {
  sessionId: string
}

export function ChatHistoryPanel({ sessionId }: ChatHistoryPanelProps) {
  const { data, isPending, isError, error } = useChatSessionMessages(sessionId)

  if (isPending) return <Notice>読み込み中… / Đang tải…</Notice>
  if (isError) return <ErrorText>{(error as Error).message}</ErrorText>
  if (data.length === 0) return <Notice>会話履歴がありません / Chưa có lịch sử hội thoại</Notice>

  return (
    <div className="space-y-2.5">
      {data.map((message) => {
        const isUser = message.sender === 'USER'
        return (
          <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
                isUser ? 'bg-teal-600 text-white' : 'border border-slate-100 bg-slate-50 text-slate-700'
              }`}
            >
              {message.message_text}
            </div>
          </div>
        )
      })}
    </div>
  )
}
