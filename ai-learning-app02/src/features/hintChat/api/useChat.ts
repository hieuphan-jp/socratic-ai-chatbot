/**
 * features/hintChat/api/useChat.ts
 *
 * JA: Hint Chat 機能の TanStack Query カスタムフック群（Type Safety 準拠）。
 * VI: Tập hợp các Custom Hook TanStack Query cho tính năng Hint Chat (Đảm bảo Type Safety).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from './chatApi'
import { queryKeys } from '@/shared/api/queryKeys'
import type { SendMessagePayload, ChatMessage } from '@/shared/types'

// JA: APIのレスポンス型定義（anyの代わりに使用）
// VI: Định nghĩa kiểu Response từ API (Thay thế cho any)
interface ChatSessionResponse {
  id: string;
  title?: string;
  created_at?: string;
}

interface SendMessageResponse {
  user_message?: ChatMessage;
  ai_message?: ChatMessage;
}

interface PaginatedResponse<T> {
  results: T[];
  count?: number;
}

/**
 * JA: チャットセッション一覧を取得するフック
 * VI: Hook lấy danh sách các phiên chat
 */
export const useChatSessions = () => {
  return useQuery({
    queryKey: queryKeys.chat.all,
    queryFn: chatApi.getSessions,
  })
}

/**
 * JA: 新しいチャットセッションを作成するフック
 * VI: Hook tạo phiên chat mới
 */
export const useCreateChatSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (title?: string): Promise<ChatSessionResponse> => {
      return await chatApi.createSession(title)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.all })
    },
  })
}

/**
 * JA: 特定セッションのメッセージ一覧を取得するフック
 * VI: Hook lấy danh sách tin nhắn của một phiên chat
 */
export const useChatMessages = (sessionId?: string) => {
  return useQuery<ChatMessage[]>({
    queryKey: ['chatMessages', sessionId],
    queryFn: async () => {
      if (!sessionId) return []
      const res = await chatApi.getMessages(sessionId)
      if (Array.isArray(res)) return res
      return (res as PaginatedResponse<ChatMessage>).results || []
    },
    enabled: !!sessionId,
    staleTime: 1000 * 60 * 5, // JA: キャッシュを5分間保持 / VI: Giữ cache 5 phút
  })
}

/**
 * JA: メッセージを送信するフック
 * VI: Hook gửi tin nhắn (Truyền sessionId vào biến mutate)
 */
export const useSendMessage = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sessionId, payload }: { sessionId: string; payload: SendMessagePayload }) =>
      chatApi.sendMessage(sessionId, payload),
    onSuccess: (data: SendMessageResponse, variables) => {
      // JA: メッセージ一覧のキャッシュに新しいメッセージを追加
      // VI: Thêm tin nhắn mới trực tiếp vào cache tin nhắn
      if (data.user_message || data.ai_message) {
        queryClient.setQueryData(['chatMessages', variables.sessionId], (oldData: ChatMessage[] | undefined) => {
          const newData = oldData ? [...oldData] : []
          if (data.user_message) newData.push(data.user_message)
          if (data.ai_message) newData.push(data.ai_message)
          return newData
        })
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.tree(variables.sessionId) })
    },
  })
}

/**
 * JA: 分岐（親ノード）を確定するフック
 * VI: Hook xác nhận rẽ nhánh (node cha)
 */
export const useConfirmParent = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      sessionId,
      messageId,
      parentMessageId,
    }: {
      sessionId: string
      messageId: string
      parentMessageId: string | null
    }) => chatApi.confirmParent(sessionId, { message_id: messageId, parent_message_id: parentMessageId }),
    onSuccess: (_updatedMsg: ChatMessage, variables) => {
      // JA: ローカルキャッシュを直接更新して即座にUIへ反映
      // VI: Cập nhật trực tiếp cache local để cố định cấu trúc rẽ nhánh vĩnh viễn
      queryClient.setQueryData(['chatMessages', variables.sessionId], (oldData: ChatMessage[] | undefined) => {
        if (!oldData) return []
        return oldData.map((m) => {
          if (String(m.id).toLowerCase() === String(variables.messageId).toLowerCase()) {
            return {
              ...m,
              parent_message: variables.parentMessageId as unknown as ChatMessage['parent_message'],
              parent_message_id: variables.parentMessageId,
              parent_confirmed: true,
            }
          }
          return m
        })
      })
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.tree(variables.sessionId) })
    },
  })
}

/**
 * JA: 思考ツリー（React Flow Graph）データを取得するフック
 * VI: Hook lấy dữ liệu Cây Tư Duy (React Flow Graph)
 */
export const useChatGraph = (sessionId: string) => {
  return useQuery({
    queryKey: queryKeys.chat.tree(sessionId),
    queryFn: () => chatApi.getGraph(sessionId),
    enabled: !!sessionId,
  })
}