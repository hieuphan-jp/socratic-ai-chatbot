import { useState } from 'react'
import { Button, Input } from '@/shared/ui'
import { useSendMessage, useCreateChatSession } from '../api/useChat'
import type { ChatMessage } from '@/shared/types'

interface HintChatViewProps {
  sessionId?: string
}

export function HintChatView({ sessionId: initialSessionId }: HintChatViewProps) {
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(initialSessionId)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')

  const createSessionMutation = useCreateChatSession()
  const sendMessageMutation = useSendMessage() // Không truyền argument vào đây nữa

  const handleSend = async () => {
    const text = draft.trim()
    if (!text || sendMessageMutation.isPending || createSessionMutation.isPending) return

    let activeSessionId = currentSessionId

    // 1. Nếu chưa có session, tạo session mới trước
    if (!activeSessionId) {
      try {
        const newSession = await createSessionMutation.mutateAsync('Phiên học mới')
        activeSessionId = newSession.id
        setCurrentSessionId(newSession.id)
      } catch (err) {
        console.error('Lỗi tạo session:', err)
        return
      }
    }

    // 2. Gửi tin nhắn kèm activeSessionId chuẩn xác
    sendMessageMutation.mutate(
      {
        sessionId: activeSessionId,
        payload: {
          message_text: text,
          action_type: 'ANSWER',
        },
      },
      {
        onSuccess: (data) => {
          setMessages((prev) => [...prev, data.user_message, data.ai_message])
          setDraft('')
        },
        onError: (error) => {
          console.error('Lỗi gửi tin nhắn:', error)
        },
      }
    )
  }

  return (
    <div className="flex flex-col h-full gap-4 max-w-2xl mx-auto p-4">
      <div className="flex-1 overflow-y-auto space-y-3 min-h-[300px] p-4 border rounded-lg bg-gray-50">
        {messages.length === 0 ? (
          <p className="text-gray-400 text-center mt-10">
            Hãy nhập câu hỏi để bắt đầu thảo luận với AI Tutor...
          </p>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`p-3 rounded-lg max-w-[80%] ${
                msg.sender === 'USER'
                  ? 'ml-auto bg-blue-600 text-white'
                  : 'mr-auto bg-white border text-gray-800'
              }`}
            >
              <p className="text-sm">{msg.message_text}</p>
            </div>
          ))
        )}
      </div>

      <div className="flex gap-2">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="質問を入力 / Nhập câu hỏi..."
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <Button
          onClick={handleSend}
          disabled={sendMessageMutation.isPending || createSessionMutation.isPending || !draft.trim()}
        >
          {sendMessageMutation.isPending || createSessionMutation.isPending
            ? '送信中...'
            : '送信 / Gửi'}
        </Button>
      </div>
    </div>
  )
}