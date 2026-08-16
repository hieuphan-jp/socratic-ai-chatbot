/**
 * shared/i18n/messages/hintChat.ts
 *
 * JA: ヒントチャット・思考ツリーまわりの文言。【この名前空間の担当者だけがこのファイルを
 *     編集する】ことで、二人で並行作業してもマージ衝突が起きないようにしている。
 *     キーは 'hintChat.' 始まり。
 *     ★現在このfeatureは枝分かれ判定の実装が別途進行中のため、ここには画面側の
 *     文言をまだ全部は移していない。担当者が画面を直すタイミングで追加していく。
 * VI: Câu chữ phần chat gợi ý / cây tư duy. 【Chỉ người phụ trách namespace này sửa
 *     file này】để hai người làm song song mà không bị xung đột khi merge.
 *     Khóa bắt đầu bằng 'hintChat.'.
 *     ★Hiện tính năng này đang được làm song song (phần phán đoán rẽ nhánh) nên chưa
 *     chuyển hết câu chữ của màn hình vào đây. Người phụ trách thêm dần khi sửa màn hình.
 */
import { defineMessages } from './defineMessages'

export const hintChatMessages = defineMessages({
  ja: {
    'hintChat.title': 'ヒントチャット',
    'hintChat.subtitle': 'AIの問いかけで学びを深める',
    'hintChat.tree.title': '思考プロセス',
    'hintChat.tree.hide': '思考ツリーを隠す',
    'hintChat.tree.show': '思考ツリーを表示',
    'hintChat.input.placeholder': '質問を入力',
    'hintChat.send': '送信',
    'hintChat.sending': '送信中…',
    'hintChat.emptyHint': '質問を送るとヒントが返ってきます',
  },
  vi: {
    'hintChat.title': 'Chat gợi ý',
    'hintChat.subtitle': 'Học sâu hơn qua câu hỏi của AI',
    'hintChat.tree.title': 'Tiến trình tư duy',
    'hintChat.tree.hide': 'Ẩn cây tư duy',
    'hintChat.tree.show': 'Hiện cây tư duy',
    'hintChat.input.placeholder': 'Nhập câu hỏi',
    'hintChat.send': 'Gửi',
    'hintChat.sending': 'Đang gửi…',
    'hintChat.emptyHint': 'Gửi câu hỏi để nhận gợi ý',
  },
  en: {
    'hintChat.title': 'Hint chat',
    'hintChat.subtitle': "Go deeper through the AI's questions",
    'hintChat.tree.title': 'Thinking process',
    'hintChat.tree.hide': 'Hide thinking tree',
    'hintChat.tree.show': 'Show thinking tree',
    'hintChat.input.placeholder': 'Type your question',
    'hintChat.send': 'Send',
    'hintChat.sending': 'Sending…',
    'hintChat.emptyHint': 'Send a question to get a hint',
  },
})
