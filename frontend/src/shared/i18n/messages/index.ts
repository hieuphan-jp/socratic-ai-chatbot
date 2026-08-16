/**
 * shared/i18n/messages/index.ts
 *
 * JA: 各名前空間の辞書を1つに束ねる。★新しい名前空間を足すときだけこのファイルを触る
 *     (文言そのものの追加は各名前空間のファイル側で行う → 衝突しない)。
 * VI: Gom từ điển của các namespace lại. ★Chỉ sửa file này khi THÊM namespace mới
 *     (thêm câu chữ thì sửa trong file của namespace đó → không xung đột).
 */
import { authMessages } from './auth'
import { commonMessages } from './common'
import { hintChatMessages } from './hintChat'
import { learningTreeMessages } from './learningTree'

export const messages = {
  ja: {
    ...commonMessages.ja,
    ...authMessages.ja,
    ...learningTreeMessages.ja,
    ...hintChatMessages.ja,
  },
  vi: {
    ...commonMessages.vi,
    ...authMessages.vi,
    ...learningTreeMessages.vi,
    ...hintChatMessages.vi,
  },
  en: {
    ...commonMessages.en,
    ...authMessages.en,
    ...learningTreeMessages.en,
    ...hintChatMessages.en,
  },
}

// JA: 画面から使えるキーの一覧。t() の引数はこの型に縛られるので、
//     存在しないキーを書くと即座に型エラーになる。
// VI: Danh sách khóa dùng được từ màn hình. Tham số của t() bị ràng buộc theo kiểu này,
//     nên viết khóa không tồn tại là báo lỗi kiểu ngay.
export type MessageKey = keyof typeof messages.ja
