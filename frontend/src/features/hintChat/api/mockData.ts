/**
 * features/hintChat/api/mockData.ts
 *
 * JA: ヒントチャットのモック応答生成。バックエンドAPIが未実装のため、送信内容に応じた
 *     固定文言を返すだけ。将来 `services.py` 側が用意でき次第、`useMutation({ mutationFn: (text) =>
 *     api.post<ChatMessage>('/hint-chat/messages/', { text }) })` に置き換える。
 * VI: Sinh phản hồi giả cho hint chat. Do backend API chưa có, chỉ trả về câu cố định theo
 *     nội dung gửi lên. Khi `services.py` sẵn sàng, thay bằng `useMutation({ mutationFn: (text) =>
 *     api.post<ChatMessage>('/hint-chat/messages/', { text }) })`.
 */

//export type ChatMessage = {
//  id: string
//  role: 'user' | 'hint'
//  text: string
//}

//// JA: 質問文に応じてそれっぽいヒントを返す簡易ロジック（モック）。
//// VI: Logic đơn giản trả hint phù hợp theo câu hỏi (mock).
//export function fetchMockHintReply(question: string): string {
//  const lower = question.toLowerCase()
//  if (lower.includes('二次方程式') || lower.includes('quadratic')) {
//    return 'ヒント: 判別式 b² - 4ac の符号を確認してみましょう。 / Gợi ý: kiểm tra dấu của biệt thức b² - 4ac.'
//  }
//  if (lower.includes('react')) {
//    return 'ヒント: まずコンポーネントの状態(state)がどこにあるか整理してみましょう。 / Gợi ý: xác định state đang nằm ở component nào trước.'
//  }
//  return 'ヒント: 問題を小さいステップに分解してみましょう。 / Gợi ý: hãy chia nhỏ vấn đề thành từng bước.'
//}

/**
 * features/chat/api/mockData.ts
 *
 * JA: チャットと思考ツリーのモックデータ生成。バックエンドAPI未実装のため仮データを使用。
 * VI: Sinh dữ liệu giả cho Chat và Sơ đồ Cây tư duy. Do backend API chưa xong nên dùng dữ liệu tạm.
 */

import type { StepNode } from '@/shared/types'

export type ChatMessage = {
  id: string
  role: 'user' | 'hint'
  text: string
}

// JA: 初期メッセージ一覧 / VI: Danh sách tin nhắn ban đầu
export const initialMockMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'hint',
    text: 'ヒント: 問題を解決するための最初のステップを入力してください。 / Gợi ý: Hãy nhập bước đầu tiên để giải quyết vấn đề.',
  },
]

// JA: Gitスタイルの思考ツリー初期データ / VI: Dữ liệu ban đầu cho sơ đồ cây kiểu Git
export const initialMockTree: StepNode[] = [
  {
    id: 'node-1',
    label: 'ステップ1: 問題の分析 / Bước 1: Phân tích bài toán',
  },
  {
    id: 'node-2',
    label: 'ステップ2: 解法の選択 / Bước 2: Chọn phương pháp giải',
    parentId: 'node-1',
  },
]

// JA: 質問文に応じてそれっぽいヒントを返す簡易ロジック（モック）。
// VI: Logic đơn giản trả hint phù hợp theo câu hỏi (mock).
export function fetchMockHintReply(question: string): string {
  const lower = question.toLowerCase()

  if (lower.includes('二次方程式') || lower.includes('quadratic')) {
    return 'ヒント: 判別式 b² - 4ac の符号を確認してみましょう。 / Gợi ý: Kiểm tra dấu của biệt thức b² - 4ac.'
  }
  if (lower.includes('react')) {
    return 'ヒント: まずコンポーネントの状態(state)がどこにあるか整理してみましょう。 / Gợi ý: Xác định state đang nằm ở component nào trước.'
  }
  if (lower.includes('別のアプローチ') || lower.includes('cách khác')) {
    return 'ヒント: 別の視点から問題を分解してみましょう。 / Gợi ý: Hãy thử chia nhỏ bài toán theo một góc nhìn khác.'
  }
  if (lower.includes('簡単') || lower.includes('giải thích lại') || lower.includes('dễ hơn')) {
    return 'ヒント: よりシンプルな例えで考えてみましょう。 / Gợi ý: Hãy suy nghĩ bằng một ví dụ đơn giản hơn.'
  }

  return 'ヒント: 問題を小さいステップに分解してみましょう。 / Gợi ý: Hãy chia nhỏ vấn đề thành từng bước.'
}

