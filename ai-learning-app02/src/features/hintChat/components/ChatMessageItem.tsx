/**
 * features/hintChat/components/ChatMessageItem.tsx
 *
 * JA: メッセージアイテム表示コンポーネント (日英対応)
 * VI: Component hiển thị từng tin nhắn chat (Hỗ trợ Việt - Nhật)
 */

import React from 'react'
import type { ChatMessage } from '@/shared/types'
import { BranchConfirmBanner } from './BranchConfirmBanner'

interface ChatMessageItemProps {
  message: ChatMessage
  messages: ChatMessage[]
  index: number
  currentSessionId?: string
  confirmParentMutation: {
    mutate: (variables: {
      sessionId: string
      messageId: string
      parentMessageId: string | null
    }) => void
    isPending: boolean
  }
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  messages,
  index,
  currentSessionId,
  confirmParentMutation,
}) => {
  const senderRole = message.sender || message.node_type || ''
  const isUser = senderRole.toUpperCase() === 'USER'
  const textContent = message.message_text || ''

  if (!textContent.trim()) return null

  // Tìm tin nhắn của người dùng ngay trước đó
  const userMsgsBefore = messages
    .slice(0, index)
    .filter((m) => (m.sender || m.node_type || '').toUpperCase() === 'USER')
  
  const immediatePrevUserMsg =
    userMsgsBefore.length > 0 ? userMsgsBefore[userMsgsBefore.length - 1] : null

  // Kiểm tra gợi ý rẽ nhánh từ AI
  const rawSuggestedParent = message.suggested_parent_id
  const suggestedParentIdStr =
    typeof rawSuggestedParent === 'object' && rawSuggestedParent !== null
      ? String((rawSuggestedParent as { id: string }).id).toLowerCase()
      : String(rawSuggestedParent || '').toLowerCase()

  const needsBranchConfirm =
    isUser &&
    !message.parent_confirmed &&
    Boolean(suggestedParentIdStr) &&
    suggestedParentIdStr !==
      (immediatePrevUserMsg ? String(immediatePrevUserMsg.id).toLowerCase() : '')

  const suggestedParentMsg = needsBranchConfirm
    ? messages.find((m) => String(m.id).toLowerCase() === suggestedParentIdStr) || null
    : null

  // Chặn copy nội dung tin nhắn của AI
  const handleCopy = (e: React.ClipboardEvent) => {
    if (!isUser) {
      e.preventDefault()
      alert(
        'JA: AIメッセージはコピーできません。 / VI: Không thể copy tin nhắn từ AI.'
      )
    }
  }

  return (
    <>
      <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div
          onCopy={handleCopy}
          className={`max-w-[85%] rounded-lg px-3.5 py-2.5 text-xs leading-relaxed whitespace-pre-wrap select-text ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'border border-gray-200 bg-gray-100 text-gray-800'
          }`}
        >
          {textContent}
        </div>
      </div>

      {/* Banner gợi ý rẽ nhánh nếu có */}
      {needsBranchConfirm && currentSessionId && (
        <BranchConfirmBanner
          message={message}
          suggestedParentMsg={suggestedParentMsg}
          suggestedParentIdStr={suggestedParentIdStr}
          isPending={confirmParentMutation.isPending}
          onConfirm={confirmParentMutation.mutate}
          currentSessionId={currentSessionId}
        />
      )}
    </>
  )
}