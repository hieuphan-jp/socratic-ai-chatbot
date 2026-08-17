/**
 * shared/i18n/messages/common.ts
 *
 * JA: どの機能からも使う共通文言(状態表示・汎用ボタン・共通ラベル)。
 *     ★ここは全員が触るファイルなので、機能固有の文言は入れないこと
 *     (機能固有は learningTree.ts / hintChat.ts など自分の名前空間へ)。
 *     キーは必ず 'common.' で始める(名前空間の衝突を防ぐため)。
 * VI: Câu chữ dùng chung cho mọi tính năng (trạng thái, nút phổ thông, nhãn chung).
 *     ★File này ai cũng đụng vào, nên KHÔNG đặt câu chữ riêng của tính năng ở đây
 *     (cái riêng thì để ở namespace của mình: learningTree.ts / hintChat.ts...).
 *     Khóa luôn bắt đầu bằng 'common.' (tránh trùng giữa các namespace).
 */
import { defineMessages } from './defineMessages'

export const commonMessages = defineMessages({
  ja: {
    'common.loading': '読み込み中…',
    'common.empty': 'まだありません',
    'common.notFound': '該当なし',
    'common.save': '保存する',
    'common.cancel': 'キャンセル',
    'common.close': '閉じる',
    'common.back': '戻る',
    'common.search': 'キーワードで検索',
    'common.retry': 'やり直す',
    'common.language': '言語',
    // JA: {status} はHTTPステータスコード(t の第2引数で渡す)。サーバが detail を
    //     返さなかった時の通信エラーの既定文言(shared/api/client.ts)。
    // VI: {status} là mã HTTP status (truyền qua tham số thứ 2 của t). Câu chữ mặc định
    //     khi server không trả detail (shared/api/client.ts).
    'common.requestFailed': 'リクエストに失敗しました ({status})',
  },
  vi: {
    'common.loading': 'Đang tải…',
    'common.empty': 'Chưa có',
    'common.notFound': 'Không tìm thấy',
    'common.save': 'Lưu',
    'common.cancel': 'Hủy',
    'common.close': 'Đóng',
    'common.back': 'Quay lại',
    'common.search': 'Tìm theo từ khóa',
    'common.retry': 'Thử lại',
    'common.language': 'Ngôn ngữ',
    'common.requestFailed': 'Yêu cầu thất bại ({status})',
  },
  en: {
    'common.loading': 'Loading…',
    'common.empty': 'Nothing here yet',
    'common.notFound': 'No matches',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.close': 'Close',
    'common.back': 'Back',
    'common.search': 'Search by keyword',
    'common.retry': 'Retry',
    'common.language': 'Language',
    'common.requestFailed': 'Request failed ({status})',
  },
})
