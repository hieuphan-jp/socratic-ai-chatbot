/**
 * shared/api/queryKeys.ts
 *
 * JA: ★TanStack Query のクエリキーを一元管理する。キーを文字列で散らすと
 *     無効化(invalidate)の対象がズレてバグる。ここで定義したものだけを使うこと。
 *     新しい feature はここにキーを1グループ追加してから使う。
 * VI: ★Quản lý tập trung query key của TanStack Query. Nếu rải key dạng chuỗi khắp nơi,
 *     đối tượng invalidate sẽ lệch và gây bug. Chỉ dùng key định nghĩa ở đây.
 *     Feature mới thêm 1 nhóm key vào đây trước khi dùng.
 */
export const queryKeys = {
  // JA: 現在ユーザー。VI: User hiện tại.
  me: ['me'] as const,

  // JA: 各機能のキーはここにグループを追加する。例（CONVENTIONS.md §5 参照）:
  //     items: { all: ['items'] as const, list: () => [...queryKeys.items.all, 'list'] as const },
  // VI: Thêm nhóm key của từng tính năng ở đây. Ví dụ (xem CONVENTIONS.md §5):
  //     items: { all: ['items'] as const, list: () => [...queryKeys.items.all, 'list'] as const },
}
