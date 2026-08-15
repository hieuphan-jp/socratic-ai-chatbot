/**
 * features/hintChat/components/ChatMessageItem.tsx
 *
 * JA: メッセージアイテム表示コンポーネント (スタイリング調整・左右配置固定)
 * VI: Component hiển thị từng tin nhắn chat (Căn chỉnh style & Cố định vị trí trái/phải)
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
  // JA: 送信者の vai trò を取得 / VI: Lấy vai trò người gửi
  const senderRole = message.sender || message.node_type || ''
  const isUser = senderRole.toUpperCase() === 'USER'
  const textContent = message.message_text || ''

  if (!textContent.trim()) return null

  // JA: 直前のユーザーメッセージを取得 / VI: Tìm tin nhắn của người dùng ngay trước đó
  const userMsgsBefore = messages
    .slice(0, index)
    .filter((m) => (m.sender || m.node_type || '').toUpperCase() === 'USER')
  
  const immediatePrevUserMsg =
    userMsgsBefore.length > 0 ? userMsgsBefore[userMsgsBefore.length - 1] : null

  // JA: AIからの分岐提案を確認 / VI: Kiểm tra gợi ý rẽ nhánh từ AI
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

  // JA: AIメッセージのコピー防止 / VI: Chặn copy nội dung tin nhắn của AI
  const handleCopy = (e: React.ClipboardEvent) => {
    if (!isUser) {
      e.preventDefault()
      alert(
        'JA: AIメッセージはコピーできません。 / VI: Không thể copy tin nhắn từ AI.'
      )
    }
  }

  return (
    <div className="flex w-full flex-col my-1">
      {/* 
        JA: w-full と justify-start (AI) / justify-end (User) で左右に確実によせる 
        VI: Sử dụng w-full cùng justify-start (AI) hoặc justify-end (User) để ép tin nhắn dạt hẳn sang 2 bên
      */}
      <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div
          onCopy={handleCopy}
          className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed whitespace-pre-wrap text-left select-text shadow-sm ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-xs'
              : 'border border-gray-200 bg-gray-100 text-gray-800 rounded-bl-xs'
          }`}
        >
          {textContent}
        </div>
      </div>

      {/* JA: 分岐確認バナー / VI: Banner gợi ý rẽ nhánh nếu có */}
      {needsBranchConfirm && currentSessionId && (
        <div className="mt-1 w-full">
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