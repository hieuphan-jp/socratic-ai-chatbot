/**
 * features/hintChat/components/ChatMessageItem.tsx
 *
 * JA: メッセージアイテム表示コンポーネント (日英対応・左揃え修正版)
 * VI: Component hiển thị từng tin nhắn chat (Đã sửa lỗi căn lề trái và loại bỏ any)
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

  // Kiểm tra gợi ý rẽ nhánh từ AI (Trích xuất Type-safe)
  const rawSuggestedParent = message.suggested_parent_id
  let suggestedParentIdStr = ''

  if (typeof rawSuggestedParent === 'object' && rawSuggestedParent !== null && 'id' in rawSuggestedParent) {
    suggestedParentIdStr = String((rawSuggestedParent as { id: string | number }).id).toLowerCase()
  } else if (typeof rawSuggestedParent === 'string' || typeof rawSuggestedParent === 'number') {
    suggestedParentIdStr = String(rawSuggestedParent).toLowerCase()
  }

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
    <div className={`flex w-full flex-col ${isUser ? 'items-end' : 'items-start'} mb-3 text-left`}>
      {/* Khung chứa nội dung tin nhắn: User bên phải, AI/System lề trái */}
      <div
        onCopy={handleCopy}
        className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-xs leading-relaxed whitespace-pre-wrap text-left break-words ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none self-end select-text'
            : 'border border-gray-200 bg-gray-100 text-gray-800 rounded-bl-none self-start select-none'
        }`}
      >
        {textContent}
      </div>

      {/* Banner gợi ý rẽ nhánh nếu có */}
      {needsBranchConfirm && currentSessionId && (
        <div className="w-full max-w-[85%] self-end mt-1">
          <BranchConfirmBanner
            message={message}
            suggestedParentMsg={suggestedParentMsg}
            suggestedParentIdStr={suggestedParentIdStr}
            isPending={confirmParentMutation.isPending}
            onConfirm={confirmParentMutation.mutate}
            currentSessionId={currentSessionId}
          />
        </div>
      )}
    </div>
  )
}