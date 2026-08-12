/**
 * features/hintChat/components/HintChatView.tsx
 *
 * JA: ヒントを対話形式で受け取るチャット画面部品（モック）。送信するとユーザー発言を追加し、
 *     少し遅れてモックのヒント応答を追加する。実API化までの見た目確認用。
 * VI: Component chat nhận hint theo dạng hội thoại (mock). Gửi thì thêm lời của user, sau đó
 *     thêm phản hồi hint giả với độ trễ nhỏ. Dùng để xem giao diện trước khi có API thật.
 */
//import { useState } from 'react'

//import { Button, Input, Notice } from '@/shared/ui'

//import { fetchMockHintReply, type ChatMessage } from '../api/mockData'

//let nextId = 0
//function newId() {
//  nextId += 1
//  return `msg-${nextId}`
//}

//export function HintChatView() {
//  const [messages, setMessages] = useState<ChatMessage[]>([])
//  const [draft, setDraft] = useState('')
//  const [waiting, setWaiting] = useState(false)

//  function handleSend() {
//    const text = draft.trim()
//    if (!text || waiting) return

//    const userMessage: ChatMessage = { id: newId(), role: 'user', text }
//    setMessages((prev) => [...prev, userMessage])
//    setDraft('')
//    setWaiting(true)

//    // JA: モックなので setTimeout で「考え中」を演出するだけ。
//    // VI: Vì là mock nên chỉ dùng setTimeout để giả lập trạng thái "đang suy nghĩ".
//    setTimeout(() => {
//      const hint: ChatMessage = { id: newId(), role: 'hint', text: fetchMockHintReply(text) }
//      setMessages((prev) => [...prev, hint])
//      setWaiting(false)
//    }, 500)
//  }

//  return (
//    <div style={{ display: 'grid', gap: 12 }}>
//      <div
//        style={{
//          minHeight: 240,
//          border: '1px solid #ddd',
//          borderRadius: 8,
//          padding: 12,
//          display: 'grid',
//          gap: 8,
//          alignContent: 'start',
//        }}
//      >
//        {messages.length === 0 && <Notice>質問を送るとヒントが返ってきます / Gửi câu hỏi để nhận gợi ý</Notice>}
//        {messages.map((m) => (
//          <div
//            key={m.id}
//            style={{
//              justifySelf: m.role === 'user' ? 'end' : 'start',
//              background: m.role === 'user' ? '#dbeafe' : '#f1f5f9',
//              borderRadius: 8,
//              padding: '8px 12px',
//              maxWidth: '80%',
//              fontSize: 14,
//            }}
//          >
//            {m.text}
//          </div>
//        ))}
//        {waiting && <Notice>ヒントを考え中… / Đang nghĩ gợi ý…</Notice>}
//      </div>
//      <div style={{ display: 'flex', gap: 8 }}>
//        <Input
//          placeholder="質問を入力 / Nhập câu hỏi"
//          value={draft}
//          onChange={(e) => setDraft(e.target.value)}
//          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
//          style={{ flex: 1 }}
//        />
//        <Button onClick={handleSend} disabled={waiting || !draft.trim()}>
//          送信 / Gửi
//        </Button>
//      </div>
//    </div>
//  )
//}

/**
 * features/hintChat/components/HintChatView.tsx
 *
 * JA: ヒントチャット画面部品（思考ツリー表示機能付き）。
 * VI: Component chat nhận hint theo dạng hội thoại (kèm tính năng xem sơ đồ cây tư duy).
 */
import { useState } from 'react'

import type { StepNode } from '@/shared/types'
import { Button, Input, Notice } from '@/shared/ui'

import { fetchMockHintReply, initialMockTree, type ChatMessage } from '../api/mockData'
import { TreeOverview } from './TreeOverview'

let nextId = 0
function newId() {
  nextId += 1
  return `msg-${nextId}`
}

export function HintChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [waiting, setWaiting] = useState(false)

  // JA: 思考ツリーの状態管理と表示フラグ / VI: Quản lý state cây tư duy và flag ẩn/hiện
  const [treeNodes, setTreeNodes] = useState<StepNode[]>(initialMockTree)
  const [showTree, setShowTree] = useState(false)

  function handleSend() {
    const text = draft.trim()
    if (!text || waiting) return

    const userMessage: ChatMessage = { id: newId(), role: 'user', text }
    setMessages((prev) => [...prev, userMessage])
    setDraft('')
    setWaiting(true)

    // JA: モックなので setTimeout で「考え中」を演出する。
    // VI: Vì là mock nên chỉ dùng setTimeout để giả lập trạng thái "đang suy nghĩ".
    setTimeout(() => {
      const hintText = fetchMockHintReply(text)
      const hint: ChatMessage = { id: newId(), role: 'hint', text: hintText }
      setMessages((prev) => [...prev, hint])

      // JA: メッセージ送信時、思考ツリーに新しいステップを追加する（デモ用）
      // VI: Mỗi lần gửi câu hỏi/trả lời, tự động thêm 1 bước mới vào sơ đồ cây (dùng cho demo)
      setTreeNodes((prev) => [
        ...prev,
        {
          id: `step-${prev.length + 1}`,
          step_number: prev.length + 1,
          label: text,
        },
      ])

      setWaiting(false)
    }, 500)
  }

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      {/* JA: ヘッダー・ツリー切り替えボタン / VI: Thanh công cụ bật/tắt Cây tư duy */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 14, fontStyle: 'italic', color: '#666' }}>
          Hint Chat Session / Phiên gợi ý
        </span>
        <Button onClick={() => setShowTree((prev) => !prev)}>
          {showTree ? '🌿 思考ツリーを隠す / Ẩn cây tư duy' : '🌿 思考ツリーを表示 / Xem cây tư duy'}
        </Button>
      </div>

      {/* JA: チャットと思考ツリーのレイアウト / VI: Bố cục chính chứa Khung Chat & Cây tư duy */}
      <div style={{ display: 'grid', gridTemplateColumns: showTree ? '1fr 280px' : '1fr', gap: 12 }}>
        {/* Khung Chat chính */}
        <div
          style={{
            minHeight: 320,
            border: '1px solid #ddd',
            borderRadius: 8,
            padding: 12,
            display: 'grid',
            gap: 8,
            alignContent: 'start',
            maxHeight: 480,
            overflowY: 'auto',
          }}
        >
          {messages.length === 0 && (
            <Notice>質問を送るとヒントが返ってきます / Gửi câu hỏi để nhận gợi ý</Notice>
          )}
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

        {/* Overview Cây tư duy (Hiển thị khi click nút Toggle) */}
        {showTree && (
          <div
            style={{
              border: '1px solid #ddd',
              borderRadius: 8,
              padding: 12,
              background: '#fafafa',
              maxHeight: 480,
              overflowY: 'auto',
            }}
          >
            <TreeOverview treeNodes={treeNodes} />
          </div>
        )}
      </div>

      {/* Khung nhập tin nhắn */}
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