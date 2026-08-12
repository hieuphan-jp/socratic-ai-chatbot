/**
 * features/chat/api/useChat.ts
 *
 * JA: チャット機能のカスタムフック（TanStack Query による状態管理）。
 * VI: Custom hooks cho tính năng Chat (quản lý state qua TanStack Query).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/shared/api/queryKeys'
import { chatApi } from './chatApi'

// JA: メッセージ一覧取得フック / VI: Hook lấy danh sách tin nhắn
export const useChatMessages = () => {
  return useQuery({
    queryKey: queryKeys.chat.messages('session-1'),
    queryFn: () => chatApi.getMessages(),
  })
}

// JA: 思考ツリー取得フック / VI: Hook lấy dữ liệu cây tư duy
export const useChatTree = () => {
  return useQuery({
    queryKey: queryKeys.chat.tree('session-1'),
    queryFn: () => chatApi.getTree(),
  })
}

// JA: メッセージ送信フック / VI: Hook gửi tin nhắn
export const useSendMessage = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (text: string) => chatApi.sendMessage(text),
    onSuccess: () => {
      // JA: キャッシュを無効化して最新状態にする / VI: Invalidate cache để cập nhật dữ liệu mới nhất
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.messages('session-1') })
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.tree('session-1') })
    },
  })
}