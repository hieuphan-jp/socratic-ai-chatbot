/**
 * features/chat/api/chatApi.ts
 *
 * JA: チャットAPI処理（モック動作）。将来バックエンド準備後に本APIに差し替える。
 * VI: Xử lý API Chat (chạy mock). Tương lai sau khi backend sẵn sàng sẽ thay bằng API thật.
 */

import type { StepNode } from '@/shared/types'
import {
  type ChatMessage,
  fetchMockHintReply,
  initialMockMessages,
  initialMockTree,
} from './mockData'

let localMessages = [...initialMockMessages]
let localTree = [...initialMockTree]

export const chatApi = {
  // JA: メッセージ一覧を取得 / VI: Lấy danh sách tin nhắn
  getMessages: async (): Promise<ChatMessage[]> => {
    return Promise.resolve(localMessages)
  },

  // JA: 思考ツリーを取得 / VI: Lấy sơ đồ cây tư duy
  getTree: async (): Promise<StepNode[]> => {
    return Promise.resolve(localTree)
  },

  // JA: メッセージ送信とAI応答生成 / VI: Gửi tin nhắn và sinh phản hồi AI
  sendMessage: async (text: string): Promise<ChatMessage> => {
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      text,
    }
    localMessages.push(userMsg)

    // JA: AIのヒント応答を生成 / VI: Sinh câu trả lời gợi ý của AI
    const replyText = fetchMockHintReply(text)
    const aiMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'hint',
      text: replyText,
    }
    localMessages.push(aiMsg)

    // JA: 「cách khác」が含まれる場合、ツリーに分岐ノードを追加
    // VI: Nếu chứa từ "cách khác" hoặc "別のアプローチ", thêm node rẽ nhánh vào sơ đồ cây
    const lower = text.toLowerCase()
    if (lower.includes('cách khác') || lower.includes('別のアプローチ')) {
      localTree.push({
        id: `node-${Date.now()}`,
        step_number: localTree.length + 1,
        label: '分岐: 別の解法アプローチ / Nhánh: Phương pháp tiếp cận khác',
        parentId: 'node-1',
      })
    }

    return Promise.resolve(aiMsg)
  },
}