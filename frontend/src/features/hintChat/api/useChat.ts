import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from './chatApi'
import { queryKeys } from '@/shared/api/queryKeys'
import type { SendMessagePayload, Topic, KnowledgeNodeSummary } from '@/shared/types'

// JA: ★学習木はTopicが入れ子(フォルダ)構造。topicId=nullならルート直下、
//     指定すればそのTopic直下の子Topic・知識ノードを返す(フォルダを開く操作)。
// VI: ★Cây học tập có cấu trúc Topic lồng nhau (thư mục). topicId=null là gốc,
//     chỉ định thì trả về Topic con/knowledge node trực thuộc (thao tác mở thư mục).
export const useTopicFolder = (topicId: string | null) => {
  return useQuery({
    queryKey: topicId ? queryKeys.topics.children(topicId) : queryKeys.topics.list(),
    queryFn: async (): Promise<{ topics: Topic[]; nodes: KnowledgeNodeSummary[] }> => {
      if (!topicId) {
        const topics = await chatApi.getRootTopics()
        return { topics, nodes: [] }
      }
      return chatApi.getTopicChildren(topicId)
    },
  })
}

// Hook tạo Topic mới (parentId=null nếu tạo ở gốc, ngược lại tạo lồng dưới parentId)
export const useCreateTopic = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ name, parentId }: { name: string; parentId: string | null }) =>
      chatApi.createTopic(name, parentId),
    onSuccess: (_, variables) => {
      const key = variables.parentId
        ? queryKeys.topics.children(variables.parentId)
        : queryKeys.topics.list()
      queryClient.invalidateQueries({ queryKey: key })
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