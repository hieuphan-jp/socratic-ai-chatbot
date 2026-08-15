/**
 * features/hintChat/components/BranchConfirmBanner.tsx
 *
 * JA: 分岐確認UIコンポーネント (日英対応版)
 * VI: Component hiển thị khung gợi ý rẽ nhánh cây tư duy (Hỗ trợ Việt - Nhật)
 */

import React from 'react'
import type { ChatMessage } from '@/shared/types'

interface BranchConfirmBannerProps {
  message: ChatMessage
  suggestedParentMsg: ChatMessage | null
  suggestedParentIdStr: string
  isPending: boolean
  onConfirm: (variables: {
    sessionId: string
    messageId: string
    parentMessageId: string | null
  }) => void
  currentSessionId: string
}

export const BranchConfirmBanner: React.FC<BranchConfirmBannerProps> = ({
  message,
  suggestedParentMsg,
  suggestedParentIdStr,
  isPending,
  onConfirm,
  currentSessionId,
}) => {
  // Xử lý đồng ý rẽ nhánh theo gợi ý từ AI
  const handleAcceptBranch = () => {
    onConfirm({
      sessionId: currentSessionId,
      messageId: String(message.id),
      parentMessageId: suggestedParentIdStr || null,
    })
  }

  // Xử lý giữ nguyên parent hiện tại
  const handleKeepOriginal = () => {
    const rawMsgParent = message.parent_message_id || message.parent_message
    const currentParentId =
      typeof rawMsgParent === 'object' && rawMsgParent !== null
        ? String((rawMsgParent as ChatMessage).id).toLowerCase()
        : String(rawMsgParent || '').toLowerCase()

    onConfirm({
      sessionId: currentSessionId,
      messageId: String(message.id),
      parentMessageId: currentParentId || null,
    })
  }

  const suggestedText = suggestedParentMsg?.message_text || ''
  const truncatedText =
    suggestedText.length > 25 ? `${suggestedText.substring(0, 25)}...` : suggestedText || '旧メッセージ / Câu thoại cũ'

  return (
    <div className="ml-auto my-1 mb-2 max-w-[85%] rounded-lg border border-blue-300 bg-blue-50 p-2.5 text-xs text-blue-900 shadow-sm">
      <div className="mb-1.5 font-medium leading-relaxed">
        💡 AI Gợi ý: Câu hỏi này có vẻ liên quan đến câu hỏi trước đó / AIの提案: この質問は前の質問に関連しているようです:{' '}
        <i className="font-normal text-blue-800">"{truncatedText}"</i>.
      </div>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={handleAcceptBranch}
          disabled={isPending}
          className="rounded bg-blue-600 px-2.5 py-1 text-[11px] font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          🌿 分岐を承認 / Đồng ý rẽ nhánh
        </button>
        <button
          type="button"
          onClick={handleKeepOriginal}
          disabled={isPending}
          className="rounded border border-gray-300 bg-white px-2.5 py-1 text-[11px] text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50 cursor-pointer"
        >
          そのまま維持 / Giữ nguyên
        </button>
      </div>
    </div>
  )
}