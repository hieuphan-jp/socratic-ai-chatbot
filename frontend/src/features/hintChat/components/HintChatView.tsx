/**
 * features/hintChat/components/HintChatView.tsx
 *
 * JA: ヒントを対話形式で受け取るチャット画面部品（モック）。送信するとユーザー発言を追加し、
 *     少し遅れてモックのヒント応答を追加する。実API化までの見た目確認用。
 * VI: Component chat nhận hint theo dạng hội thoại (mock). Gửi thì thêm lời của user, sau đó
 *     thêm phản hồi hint giả với độ trễ nhỏ. Dùng để xem giao diện trước khi có API thật.
 */
import { useState } from 'react'

import { Button, Input, Notice } from '@/shared/ui'

import { fetchMockHintReply, type ChatMessage } from '../api/mockData'

let nextId = 0
function newId() {
  nextId += 1
  return `msg-${nextId}`
}

export function HintChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [waiting, setWaiting] = useState(false)

  function handleSend() {
    const text = draft.trim()
    if (!text || waiting) return

    const userMessage: ChatMessage = { id: newId(), role: 'user', text }
    setMessages((prev) => [...prev, userMessage])
    setDraft('')
    setWaiting(true)

    // JA: モックなので setTimeout で「考え中」を演出するだけ。
    // VI: Vì là mock nên chỉ dùng setTimeout để giả lập trạng thái "đang suy nghĩ".
    setTimeout(() => {
      const hint: ChatMessage = { id: newId(), role: 'hint', text: fetchMockHintReply(text) }
      setMessages((prev) => [...prev, hint])
      setWaiting(false)
    }, 500)
  }

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div
        style={{
          minHeight: 240,
          border: '1px solid #ddd',
          borderRadius: 8,
          padding: 12,
          display: 'grid',
          gap: 8,
          alignContent: 'start',
        }}
      >
        {messages.length === 0 && <Notice>質問を送るとヒントが返ってきます / Gửi câu hỏi để nhận gợi ý</Notice>}
        {messages.map((m) => (
          <div
            key={m.id}
            style={{
              justifySelf: m.role === 'user' ? 'end' : 'start',
              background: m.role === 'user' ? '#dbeafe' : '#f1f5f9',
              borderRadius: 8,
              padding: '8px 12px',
              maxWidth: '80%',
              fontSize: 14,
            }}
          >
            {m.text}
          </div>
        ))}
        {waiting && <Notice>ヒントを考え中… / Đang nghĩ gợi ý…</Notice>}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <Input
          placeholder="質問を入力 / Nhập câu hỏi"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          style={{ flex: 1 }}
        />
        <Button onClick={handleSend} disabled={waiting || !draft.trim()}>
          送信 / Gửi
        </Button>
      </div>
    </div>
  )
}
