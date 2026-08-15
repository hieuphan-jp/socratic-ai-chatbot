/**
 * features/hintChat/api/useChat.ts
 *
 * JA: チャット関連のReact Queryカスタムフック群。
 * VI: Các custom hook React Query quản lý Chat & Tree.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from './chatApi'
import { queryKeys } from '@/shared/api/queryKeys'
import type { SendMessagePayload, ChatMessage } from '@/shared/types'

// JA: APIレスポンスの型定義
// VI: Định nghĩa type chuẩn cho response từ sendMessage API
export interface SendMessageResponse {
  user_message: ChatMessage
  ai_message: ChatMessage
  session_info?: {
    hint_count: number
    completed_at: string | null
  }
}

/**
 * JA: チャットセッション一覧を取得するカスタムフック
 * VI: Custom hook lấy danh sách các phiên chat
 */
export const useChatSessions = () => {
  return useQuery({
    queryKey: ['chatSessions'],
    queryFn: () => chatApi.getSessions(),
  })
}

/**
 * JA: 新規チャットセッションを作成するカスタムフック
 * VI: Custom hook tạo phiên chat mới
 */
export const useCreateChatSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (title?: string) => chatApi.createSession(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.all })
    },
  })
}

/**
 * JA: メッセージ送信フック（即時キャッシュ更新対応）
 * VI: Custom hook gửi tin nhắn (Cập nhật cache tức thì)
 */
export const useSendMessage = (currentSessionId?: string) => {
  const queryClient = useQueryClient()

  return useMutation<
    SendMessageResponse,
    Error,
    { sessionId: string; payload: SendMessagePayload }
  >({
    mutationFn: ({ sessionId, payload }) => chatApi.sendMessage(sessionId, payload),

    onSuccess: (data, variables) => {
      const activeId = currentSessionId || variables.sessionId
      // JA: APIレスポンスデータでメッセージキャッシュを直接更新
      // VI: Cập nhật trực tiếp Cache tin nhắn
      queryClient.setQueryData<ChatMessage[]>(
        ['chatMessages', activeId],
        (oldData) => {
          const newData = oldData ? [...oldData] : []
          if (data.user_message) newData.push(data.user_message)
          if (data.ai_message) newData.push(data.ai_message)
          return newData
        }
      )

      queryClient.invalidateQueries({
        queryKey: queryKeys.chat.tree(activeId),
      })
    },
  })
}

/**
 * JA: 思考ツリー取得フック
 * VI: Custom hook lấy dữ liệu Cây Tư Duy (React Flow Graph)
 */
export const useChatGraph = (sessionId: string) => {
  return useQuery({
    queryKey: queryKeys.chat.tree(sessionId),
    queryFn: () => chatApi.getGraph(sessionId),
    enabled: !!sessionId,
  })
}