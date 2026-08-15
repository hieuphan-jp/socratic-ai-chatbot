/**
 * shared/api/queryKeys.ts
 *
 * JA: ★TanStack Query のクエリキーを一元管理する。
 * VI: ★Quản lý tập trung query key của TanStack Query.
 */
export const queryKeys = {
  // VI: User hiện tại.
  me: ['me'] as const,

  // VI: Key cho tính năng Hint Chat và Cây tư duy (Step Tree / Graph).
  chat: {
    all: ['chat'] as const,
    sessions: () => [...queryKeys.chat.all, 'sessions'] as const,
    session: (sessionId: string) => [...queryKeys.chat.all, 'session', sessionId] as const,
    messages: (sessionId: string) => [...queryKeys.chat.all, 'messages', sessionId] as const,
    tree: (sessionId: string) => [...queryKeys.chat.all, 'tree', sessionId] as const,
  },

  // VI: Key cho tính năng Cây học tập (Learning Tree).
  learningTree: {
    all: ['learningTree'] as const,
    list: () => [...queryKeys.learningTree.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.learningTree.all, 'detail', id] as const,
  },
}