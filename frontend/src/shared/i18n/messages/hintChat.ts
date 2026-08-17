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
    'hintChat.session.label': 'ヒントチャットセッション',
    'hintChat.tree.title': '思考プロセス',
    'hintChat.tree.hide': '思考ツリーを隠す',
    'hintChat.tree.show': '思考ツリーを表示',
    'hintChat.tree.dragHint': 'ノードをドラッグできます',
    'hintChat.input.placeholder': '質問を入力(Shift+Enterで改行)',
    'hintChat.send': '送信',
    'hintChat.sending': '送信中…',
    'hintChat.thinking': '考え中…',
    'hintChat.emptyHint': '質問を送るとヒントが返ってきます',
    'hintChat.complete.review': '復習を完了する',
    'hintChat.complete.saveAsNode': '学習を完了して知識ノードとして保存',
    'hintChat.complete.folderPrompt':
      '学習木のどのフォルダに保存するか選んでください（フォルダを開いて絞り込めます）',
    // JA: {title} は保存された知識ノードのタイトル(t の第2引数で渡す)。
    // VI: {title} là tiêu đề knowledge node vừa lưu (truyền qua tham số thứ 2 của t).
    'hintChat.complete.saved': '知識ノード「{title}」として保存しました',
    'hintChat.copyBlocked': 'AIのヒントメッセージはコピーできません',
    // JA: {quote} は関連する過去の発言の抜粋(t の第2引数で渡す)。
    // VI: {quote} là trích đoạn phát ngôn cũ liên quan (truyền qua tham số thứ 2 của t).
    'hintChat.branch.suggestion':
      'この質問は、以前の「{quote}」に関連しているようです。この話題から思考ツリーを分岐しますか？',
    'hintChat.branch.oldMessageFallback': '過去の発言',
    'hintChat.branch.confirm': '分岐する',
    'hintChat.branch.keep': 'そのままにする',
    'hintChat.step.pendingParent': '親ステップの確認待ち',
    'hintChat.folderPicker.root': 'ルート',
    'hintChat.folderPicker.empty': 'このフォルダは空です',
    'hintChat.folderPicker.newFolderPlaceholder': '新しいフォルダ名',
    'hintChat.folderPicker.create': '作成',
    'hintChat.folderPicker.saveHere': 'このフォルダに保存',
  },
  vi: {
    'hintChat.title': 'Chat gợi ý',
    'hintChat.subtitle': 'Học sâu hơn qua câu hỏi của AI',
    'hintChat.session.label': 'Phiên chat gợi ý',
    'hintChat.tree.title': 'Tiến trình tư duy',
    'hintChat.tree.hide': 'Ẩn cây tư duy',
    'hintChat.tree.show': 'Hiện cây tư duy',
    'hintChat.tree.dragHint': 'Có thể kéo/thả node',
    'hintChat.input.placeholder': 'Nhập câu hỏi (Shift+Enter để xuống dòng)',
    'hintChat.send': 'Gửi',
    'hintChat.sending': 'Đang gửi…',
    'hintChat.thinking': 'Đang suy nghĩ…',
    'hintChat.emptyHint': 'Gửi câu hỏi để nhận gợi ý',
    'hintChat.complete.review': 'Hoàn thành ôn tập',
    'hintChat.complete.saveAsNode': 'Hoàn thành và lưu thành knowledge node',
    'hintChat.complete.folderPrompt':
      'Chọn lưu vào thư mục nào trong cây học tập (có thể mở thư mục để đi sâu hơn)',
    'hintChat.complete.saved': 'Đã lưu thành knowledge node "{title}"',
    'hintChat.copyBlocked': 'Không thể copy tin nhắn gợi ý từ AI',
    'hintChat.branch.suggestion':
      'Câu hỏi này có vẻ liên quan đến câu hỏi trước đó: "{quote}". Bạn có muốn rẽ nhánh cây tư duy từ câu đó không?',
    'hintChat.branch.oldMessageFallback': 'Câu thoại cũ',
    'hintChat.branch.confirm': 'Đồng ý rẽ nhánh',
    'hintChat.branch.keep': 'Giữ nguyên',
    'hintChat.step.pendingParent': 'Đang chờ xác nhận node cha',
    'hintChat.folderPicker.root': 'Gốc',
    'hintChat.folderPicker.empty': 'Thư mục này trống',
    'hintChat.folderPicker.newFolderPlaceholder': 'Tên thư mục mới',
    'hintChat.folderPicker.create': 'Tạo',
    'hintChat.folderPicker.saveHere': 'Lưu vào thư mục này',
  },
  en: {
    'hintChat.title': 'Hint chat',
    'hintChat.subtitle': "Go deeper through the AI's questions",
    'hintChat.session.label': 'Hint chat session',
    'hintChat.tree.title': 'Thinking process',
    'hintChat.tree.hide': 'Hide thinking tree',
    'hintChat.tree.show': 'Show thinking tree',
    'hintChat.tree.dragHint': 'You can drag nodes',
    'hintChat.input.placeholder': 'Type your question (Shift+Enter for a new line)',
    'hintChat.send': 'Send',
    'hintChat.sending': 'Sending…',
    'hintChat.thinking': 'Thinking…',
    'hintChat.emptyHint': 'Send a question to get a hint',
    'hintChat.complete.review': 'Complete review',
    'hintChat.complete.saveAsNode': 'Finish and save as a knowledge node',
    'hintChat.complete.folderPrompt':
      'Choose which folder in the learning tree to save this in (you can open folders to go deeper)',
    'hintChat.complete.saved': 'Saved as knowledge node "{title}"',
    'hintChat.copyBlocked': "AI hint messages can't be copied",
    'hintChat.branch.suggestion':
      'This question seems related to an earlier one: "{quote}". Branch the thinking tree from there?',
    'hintChat.branch.oldMessageFallback': 'an earlier message',
    'hintChat.branch.confirm': 'Branch here',
    'hintChat.branch.keep': 'Keep as is',
    'hintChat.step.pendingParent': 'Waiting to confirm parent step',
    'hintChat.folderPicker.root': 'Root',
    'hintChat.folderPicker.empty': 'This folder is empty',
    'hintChat.folderPicker.newFolderPlaceholder': 'New folder name',
    'hintChat.folderPicker.create': 'Create',
    'hintChat.folderPicker.saveHere': 'Save to this folder',
  },
})
