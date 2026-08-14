import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from './chatApi'
import { queryKeys } from '@/shared/api/queryKeys'
import type { SendMessagePayload } from '@/shared/types'

// Hook lấy danh sách Topic (để chọn nơi lưu knowledge node khi hoàn thành chat tự do)
export const useTopics = () => {
  return useQuery({
    queryKey: queryKeys.topics.list(),
    queryFn: chatApi.getTopics,
  })
}

// Hook tạo Topic mới
export const useCreateTopic = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => chatApi.createTopic(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.topics.list() })
    },
  })
}

// Hook lấy danh sách phiên chat
export const useChatSessions = () => {
  return useQuery({
    queryKey: queryKeys.chat.all,
    queryFn: chatApi.getSessions,
  })
}

// Hook tạo phiên chat mới
export const useCreateChatSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (title?: string) => chatApi.createSession(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.all })
    },
  })
}

// Hook gửi tin nhắn (Truyền sessionId vào biến mutate)
export const useSendMessage = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sessionId, payload }: { sessionId: string; payload: SendMessagePayload }) =>
      chatApi.sendMessage(sessionId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.tree(variables.sessionId) })
    },
  })
}

// Hook lấy dữ liệu Cây Tư Duy (React Flow Graph)
export const useChatGraph = (sessionId: string) => {
  return useQuery({
    queryKey: queryKeys.chat.tree(sessionId),
    queryFn: () => chatApi.getGraph(sessionId),
    enabled: !!sessionId,
  })
}