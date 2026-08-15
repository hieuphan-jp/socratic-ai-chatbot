/**
 * features/hintChat/components/HintChatView.tsx
 *
 * JA: ヒントチャットと思考ツリーのメイン表示コンポーネント (自動スクロール・即時反映対応)
 * VI: Component hiển thị chính của Hint Chat và Sơ đồ tư duy (Tự động cuộn & Cập nhật tức thì)
 */

import React, { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { chatApi } from '../api/chatApi'
import { useSendMessage } from '../api/useChat'
import type { ChatMessage } from '@/shared/types'

import { ChatInputForm } from './ChatInputForm'
import { ChatMessageItem } from './ChatMessageItem'
import { ThinkingTreePanel } from './ThinkingTreePanel'

interface HintChatViewProps {
  activeSessionId?: string
  onSessionCreated?: (newSessionId: string) => void
}

export const HintChatView: React.FC<HintChatViewProps> = ({
  activeSessionId: propSessionId,
  onSessionCreated,
}) => {
  const queryClient = useQueryClient()

  // JA: セッションID管理 / VI: Quản lý Session ID
  const [internalSessionId, setInternalSessionId] = useState<string | undefined>(undefined)
  const currentSessionId = propSessionId || internalSessionId

  // JA: 思考ツリーの表示切り替え / VI: Toggle ẩn/hiện sơ đồ tư duy
  const [showTree, setShowTree] = useState(true)

  // JA: メッセージ一覧の末尾要素への参照 (自動スクロール用)
  // VI: Ref đến cuối danh sách tin nhắn (Dùng cho auto-scroll)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // JA: メッセージ送信フック / VI: Hook gửi tin nhắn
  const sendMessageMutation = useSendMessage(currentSessionId)

  // JA: 新規セッション作成ミューテーション / VI: Mutation tạo phiên chat mới
  const createSessionMutation = useMutation({
    mutationFn: (title?: string) => chatApi.createSession(title || 'Hint Chat Session'),
    onSuccess: (newSession) => {
      const newId = newSession.id
      setInternalSessionId(newId)
      if (onSessionCreated) {
        onSessionCreated(newId)
      }
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] })
    },
  })

  // 1. JA: メッセージ一覧取得 / VI: Fetch danh sách tin nhắn
  const { data: messages = [], isLoading: isLoadingMessages } = useQuery<ChatMessage[]>({
    queryKey: ['chatMessages', currentSessionId],
    queryFn: async () => {
      if (!currentSessionId) return []
      const res = await chatApi.getMessages(currentSessionId)
      return Array.isArray(res) ? res : (res as unknown as { results: ChatMessage[] }).results || []
    },
    enabled: !!currentSessionId,
    staleTime: 1000 * 60 * 5,
  })

  // JA: メッセージ追加時や送信中に自動スクロール
  // VI: Tự động cuộn xuống cuối khi có tin nhắn mới hoặc đang chờ AI trả lời
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sendMessageMutation.isPending])

  // 2. JA: 親ノード確認ミューテーション / VI: Mutation xác nhận node cha (rẽ nhánh)
  const confirmParentMutation = useMutation({
    mutationFn: ({
      sessionId,
      messageId,
      parentMessageId,
    }: {
      sessionId: string
      messageId: string
      parentMessageId: string | null
    }) => chatApi.confirmParent(sessionId, { message_id: messageId, parent_message_id: parentMessageId }),
    onSuccess: (_updatedMsg, variables) => {
      queryClient.setQueryData(['chatMessages', currentSessionId], (oldData: ChatMessage[] | undefined) => {
        if (!oldData) return []
        return oldData.map((m) => {
          if (String(m.id).toLowerCase() === String(variables.messageId).toLowerCase()) {
            return {
              ...m,
              parent_message: variables.parentMessageId as unknown as ChatMessage,
              parent_message_id: variables.parentMessageId || undefined,
              parent_confirmed: true,
            }
          }
          return m
        })
      })
    },
  })

  // 3. JA: メッセージ送信ハンドラー / VI: Hàm xử lý gửi tin nhắn
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return

    let targetSessionId = currentSessionId

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
  }

  const isPending = sendMessageMutation.isPending || createSessionMutation.isPending

  return (
    <div className="w-full font-sans text-gray-800 box-border">
      
      {/* Header & Button Toggle Cây tư duy */}
      <div className="mb-3 flex items-center justify-between">
        <div className="text-xs text-gray-500 italic">
          Hint Chat Session / セッション: {currentSessionId || 'New Session / 新規'}
        </div>
        <button
          type="button"
          onClick={() => setShowTree(!showTree)}
          className="rounded-md border border-gray-300 bg-gray-100 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-200 transition-colors cursor-pointer"
        >
          🌿 {showTree ? '思考ツリーを隠す / Ẩn cây tư duy' : '思考ツリーを表示 / Hiện cây tư duy'}
        </button>
      </div>

      {/* Container chính: Cột Chat & Cột Sơ đồ tư duy */}
      <div className="mb-4 flex w-full gap-4">
        
        {/* CỘT TRÁI: Khung hiển thị tin nhắn */}
        <div className={`flex h-[480px] flex-col rounded-2xl border border-gray-200 bg-white p-4 box-border overflow-y-auto transition-all ${
          showTree ? 'flex-[1.2]' : 'w-full flex-1'
        }`}>
          {isLoadingMessages && (
            <p className="text-xs text-gray-400">Đang tải... / 読み込み中...</p>
          )}

          {!isLoadingMessages && messages.length === 0 && (
            <div className="mt-2 text-xs text-gray-400 leading-relaxed">
              質問を送るとヒントが返ってきます<br />
              Gửi câu hỏi để nhận gợi ý từ AI
            </div>
          )}

          {/* Danh sách tin nhắn */}
          <div className="flex flex-col gap-2.5">
            {Array.isArray(messages) &&
              messages.map((msg: ChatMessage, index: number) => (
                <ChatMessageItem
                  key={msg.id || index}
                  message={msg}
                  messages={messages}
                  index={index}
                  currentSessionId={currentSessionId}
                  confirmParentMutation={confirmParentMutation}
                />
              ))}

            {/* Bong bóng AI đang suy nghĩ */}
            {sendMessageMutation.isPending && (
              <div className="flex justify-start">
                <div className="rounded-lg bg-gray-100 px-3 py-2 text-xs italic text-gray-400 animate-pulse">
                  AI thinking... / AIが考え中...
                </div>
              </div>
            )}

            {/* Anchor element cho Auto-scroll */}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* CỘT PHẢI: Sơ đồ tư duy */}
        {showTree && (
          <div className="flex-1 transition-all">
            <ThinkingTreePanel messages={messages} />
          </div>
        )}
      </div>

      {/* FORM NHẬP TIN NHẮN */}
      <ChatInputForm
        onSendMessage={handleSendMessage}
        disabled={isPending}
        isPending={sendMessageMutation.isPending}
      />

    </div>
  )
}