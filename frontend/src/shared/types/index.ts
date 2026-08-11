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
