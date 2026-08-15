/**
 * features/hintChat/components/HintChatView.tsx
 *
 * JA: ヒントチャットと思考ツリーのメイン表示コンポーネント。
 * VI: Component hiển thị chính của Hint Chat và Sơ đồ tư duy.
 */

import React, { useState } from 'react'
import {
  useChatMessages,
  useSendMessage,
  useCreateChatSession,
} from '../api/useChat'
import { mapMessagesToFlow } from '../utils/flowMapper'
import { StepTreeFlow } from './StepTreeFlow'
import type { ChatMessage } from '../types'

interface HintChatViewProps {
  activeSessionId?: string
  onSessionCreated?: (newSessionId: string) => void
}

export const HintChatView: React.FC<HintChatViewProps> = ({
  activeSessionId: propSessionId,
  onSessionCreated,
}) => {
  // Local States
  const [internalSessionId, setInternalSessionId] = useState<string | undefined>(undefined)
  const [inputText, setInputText] = useState('')
  const [showTree, setShowTree] = useState(true)

  // Ưu tiên dùng propSessionId truyền từ ngoài vào, nếu không có thì dùng internalSessionId vừa tạo
  const currentSessionId = propSessionId || internalSessionId

  // Custom Hooks từ TanStack Query
  const { data: messages = [], isLoading: isLoadingMessages } = useChatMessages(currentSessionId)
  const sendMessageMutation = useSendMessage()
  const createSessionMutation = useCreateChatSession()

  // Chuyển đổi tin nhắn thành React Flow Nodes & Edges
  const { nodes, edges } = mapMessagesToFlow(messages)

  // JA: メッセージ送信ハンドラー / VI: Hàm xử lý gửi tin nhắn
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return

    let targetSessionId = currentSessionId

    // Nếu chưa có session, tạo mới trước khi gửi
    if (!targetSessionId) {
      try {
        const newSession = await createSessionMutation.mutateAsync('Hint Chat Session')
        targetSessionId = newSession.id
        setInternalSessionId(targetSessionId)
        if (onSessionCreated && targetSessionId) {
          onSessionCreated(targetSessionId)
        }
      } catch {
        return
      }
    }

    if (targetSessionId) {
      sendMessageMutation.mutate({
        sessionId: targetSessionId,
        payload: {
          message_text: text,
          action_type: 'ANSWER',
        },
      })
    }

    setInputText('')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleSendMessage(inputText)
  }

  return (
    <div style={{ width: '100%', fontFamily: 'sans-serif', color: '#333', boxSizing: 'border-box' }}>
      
      {/* Nút Toggle Ẩn/Hiện Sơ đồ tư duy */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ fontSize: '14px', color: '#666', fontStyle: 'italic' }}>
          Hint Chat Session / Phiên gợi ý
        </div>
        <button
          onClick={() => setShowTree(!showTree)}
          style={{
            padding: '6px 12px',
            fontSize: '12px',
            backgroundColor: '#f3f4f6',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          🌿 思考ツリーを隠す / {showTree ? 'Ẩn cây tư duy' : 'Hiện cây tư duy'}
        </button>
      </div>

      {/* Container chứa Cột Chat & Cột Sơ đồ tư duy */}
      <div style={{ display: 'flex', gap: '16px', width: '100%', marginBottom: '16px' }}>
        
        {/* CỘT TRÁI: Khung hiển thị chat */}
        <div
          style={{
            flex: 1.2,
            height: '480px',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            backgroundColor: '#ffffff',
            padding: '16px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            boxSizing: 'border-box',
          }}
        >
          {isLoadingMessages && <p style={{ fontSize: '12px', color: '#9ca3af' }}>Đang tải...</p>}

          {!isLoadingMessages && messages.length === 0 && (
            <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '8px' }}>
              質問を送るとヒントが返ってきます /<br />
              Gửi câu hỏi để nhận gợi ý
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {messages.map((msg: ChatMessage, index: number) => {
              const isUser = msg.sender === 'user'
              const textContent = msg.text || ''

              return (
                <React.Fragment key={msg.id || index}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: isUser ? 'flex-end' : 'flex-start',
                    }}
                  >
                    <div
                      style={{
                        maxWidth: '85%',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        fontSize: '13px',
                        lineHeight: '1.5',
                        backgroundColor: isUser ? '#2563eb' : '#f3f4f6',
                        color: isUser ? '#ffffff' : '#1f2937',
                        border: isUser ? 'none' : '1px solid #e5e7eb',
                        whiteSpace: 'pre-wrap',
                        userSelect: isUser ? 'text' : 'none',
                        WebkitUserSelect: isUser ? 'text' : 'none',
                        msUserSelect: isUser ? 'text' : 'none',
                      }}
                      onCopy={(e) => {
                        if (!isUser) {
                          e.preventDefault()
                          alert('JA: AIのヒントメッセージはコピーできません。 / VI: Không thể copy tin nhắn gợi ý từ AI.')
                        }
                      }}
                    >
                      {textContent}
                    </div>
                  </div>
                </React.Fragment>
              )
            })}

            {sendMessageMutation.isPending && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    fontSize: '13px',
                    backgroundColor: '#f3f4f6',
                    color: '#9ca3af',
                    fontStyle: 'italic',
                  }}
                >
                  Thinking...
                </div>
              </div>
            )}
          </div>
        </div>

        {/* CỘT PHẢI: Sơ đồ tư duy (StepTreeFlow component) */}
        {showTree && (
          <div
            style={{
              flex: 1,
              height: '480px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              backgroundColor: '#ffffff',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              boxSizing: 'border-box',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 'bold', margin: 0, color: '#111827' }}>
                🌿 思考プロセス / Tiến trình tư duy
              </h3>
              <span style={{ fontSize: '11px', color: '#6b7280' }}>✋ Có thể kéo/thả node</span>
            </div>

            <div style={{ flex: 1, width: '100%', border: '1px solid #f3f4f6', borderRadius: '6px' }}>
              <StepTreeFlow initialNodes={nodes} initialEdges={edges} />
            </div>
          </div>
        )}
      </div>

      {/* Form nhập liệu tin nhắn */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', width: '100%', boxSizing: 'border-box' }}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="質問を入力 / Nhập câu hỏi"
          style={{
            flex: 1,
            padding: '10px 14px',
            fontSize: '13px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            outline: 'none',
          }}
          disabled={sendMessageMutation.isPending || createSessionMutation.isPending}
        />
        <button
          type="submit"
          disabled={
            sendMessageMutation.isPending ||
            createSessionMutation.isPending ||
            !inputText.trim()
          }
          style={{
            padding: '10px 24px',
            fontSize: '13px',
            backgroundColor: '#f3f4f6',
            color: '#4b5563',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: '500',
          }}
        >
          {sendMessageMutation.isPending ? '送信中...' : '送信 / Gửi'}
        </button>
      </form>

    </div>
  )
}