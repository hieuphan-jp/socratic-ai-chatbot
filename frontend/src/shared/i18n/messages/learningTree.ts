/**
 * shared/i18n/messages/learningTree.ts
 *
 * JA: 学習木・復習まわりの文言。【この名前空間の担当者だけがこのファイルを編集する】
 *     ことで、二人で並行作業してもマージ衝突が起きないようにしている。
 *     キーは 'learningTree.' 始まり。画面に文言を足すときは、まずここにキーを追加する。
 * VI: Câu chữ phần cây học tập / ôn tập. 【Chỉ người phụ trách namespace này sửa file
 *     này】để hai người làm song song mà không bị xung đột khi merge.
 *     Khóa bắt đầu bằng 'learningTree.'. Thêm chữ lên màn hình thì thêm khóa ở đây trước.
 */
import { defineMessages } from './defineMessages'

export const learningTreeMessages = defineMessages({
  ja: {
    'learningTree.title': '学習内容ツリー',
    'learningTree.subtitle': '学んだ内容と、その定着ぐあい',
    'learningTree.view.tree': '木構造',
    'learningTree.view.timeline': 'タイムログ',
    'learningTree.retention.label': '定着中のノード',
    'learningTree.due.title': '今日の復習',
    'learningTree.due.none': '復習が必要なノードはありません',
    'learningTree.due.today': '本日',
    // JA: {days} は日数に置き換わる(t の第2引数で渡す)。
    // VI: {days} sẽ được thay bằng số ngày (truyền qua tham số thứ 2 của t).
    'learningTree.due.overdue': '{days}日超過',
    'learningTree.node.detail': 'ノードの詳細',
    'learningTree.node.tab.detail': '詳細',
    'learningTree.node.tab.chatHistory': '会話ログ',
    'learningTree.node.unlearned': '未学習（まだ復習記録がありません）',
    'learningTree.review.badge': '復習',
    'learningTree.review.start': '復習を始める',
    'learningTree.review.startFromChat': 'チャットで学習を始める',
    'learningTree.review.opening': '開いています…',
  },
  vi: {
    'learningTree.title': 'Cây nội dung đã học',
    'learningTree.subtitle': 'Nội dung đã học và mức độ ghi nhớ',
    'learningTree.view.tree': 'Cây',
    'learningTree.view.timeline': 'Nhật ký thời gian',
    'learningTree.retention.label': 'Node đã ghi nhớ',
    'learningTree.due.title': 'Ôn tập hôm nay',
    'learningTree.due.none': 'Không có node nào cần ôn tập',
    'learningTree.due.today': 'Hôm nay',
    'learningTree.due.overdue': 'Quá {days} ngày',
    'learningTree.node.detail': 'Chi tiết node',
    'learningTree.node.tab.detail': 'Chi tiết',
    'learningTree.node.tab.chatHistory': 'Lịch sử hội thoại',
    'learningTree.node.unlearned': 'Chưa học (chưa có bản ghi ôn tập)',
    'learningTree.review.badge': 'Ôn tập',
    'learningTree.review.start': 'Bắt đầu ôn tập',
    'learningTree.review.startFromChat': 'Bắt đầu học bằng chat',
    'learningTree.review.opening': 'Đang mở…',
  },
  en: {
    'learningTree.title': 'Learning tree',
    'learningTree.subtitle': 'What you learned, and how well it stuck',
    'learningTree.view.tree': 'Tree',
    'learningTree.view.timeline': 'Timeline',
    'learningTree.retention.label': 'Nodes retained',
    'learningTree.due.title': "Today's reviews",
    'learningTree.due.none': 'Nothing needs reviewing right now',
    'learningTree.due.today': 'Today',
    'learningTree.due.overdue': '{days} days overdue',
    'learningTree.node.detail': 'Node details',
    'learningTree.node.tab.detail': 'Details',
    'learningTree.node.tab.chatHistory': 'Conversation log',
    'learningTree.node.unlearned': 'Not studied yet (no review history)',
    'learningTree.review.badge': 'Review',
    'learningTree.review.start': 'Start review',
    'learningTree.review.startFromChat': 'Start learning in chat',
    'learningTree.review.opening': 'Opening…',
  },
})
