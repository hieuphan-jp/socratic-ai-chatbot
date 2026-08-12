/**
 * shared/types/index.ts
 *
 * JA: 複数の feature で共有する型を置く。features 固有の型は各 feature 内に置くこと。
 *     バックエンドのシリアライザ出力と形を合わせる（ズレたら型エラーで気づける）。
 * VI: Đặt các kiểu dùng chung nhiều feature. Kiểu riêng của feature để trong feature đó.
 *     Khớp hình dạng với output serializer backend (lệch sẽ báo lỗi kiểu để phát hiện).
 */

// JA: 現在ユーザー。accounts.UserSerializer と対応。
// VI: User hiện tại, tương ứng accounts.UserSerializer.
export type User = {
  id: number
  username: string
  email: string
}

// JA: 各機能のドメイン型はここに追加する（バックエンドのシリアライザ出力と形を合わせる）。
// VI: Thêm kiểu domain của từng tính năng ở đây (khớp hình dạng với output serializer backend).

// JA: チャット機能・思考ツリーに関する型定義（バックエンドのデータ構造に合わせる）。
// VI: Định nghĩa kiểu dữ liệu cho tính năng Chat và Cây tư duy (khớp cấu trúc dữ liệu backend).

export type SenderType = 'USER' | 'AI'

export type ChatMessage = {
  id: string
  session: string
  sender: SenderType
  message_text: string
  is_hint: boolean
  sent_at: string
}

export type ChatSession = {
  id: string
  user: number
  attempt: string
  title: string
  created_at: string
}

// JA: Chat機能専用の思考ツリーノード（ユーザーが通過したステップのみを記録）。
// VI: Node cây tư duy dành riêng cho feature Chat (chỉ ghi nhận các bước người dùng đã đi qua).
export type StepNode = {
  id: string
  step_number: number      // JA: ステップ番号 / VI: Thứ tự bước (1, 2, 3...)
  label: string            // JA: ステップの簡潔な概要 / VI: Tóm tắt ngắn gọn của bước
  parentId?: string        // JA: 親ステップID / VI: ID bước trước đó
  childrenIds?: string[]   // JA: 子ステップID群 / VI: Danh sách ID bước con (nếu có chia nhánh)
}