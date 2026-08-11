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

export type ChatMessage = {
  id: string
  role: 'user' | 'hint'
  text: string
}

// JA: 質問文に応じてそれっぽいヒントを返す簡易ロジック（モック）。
// VI: Logic đơn giản trả hint phù hợp theo câu hỏi (mock).
export function fetchMockHintReply(question: string): string {
  const lower = question.toLowerCase()
  if (lower.includes('二次方程式') || lower.includes('quadratic')) {
    return 'ヒント: 判別式 b² - 4ac の符号を確認してみましょう。 / Gợi ý: kiểm tra dấu của biệt thức b² - 4ac.'
  }
  if (lower.includes('react')) {
    return 'ヒント: まずコンポーネントの状態(state)がどこにあるか整理してみましょう。 / Gợi ý: xác định state đang nằm ở component nào trước.'
  }
  return 'ヒント: 問題を小さいステップに分解してみましょう。 / Gợi ý: hãy chia nhỏ vấn đề thành từng bước.'
}
