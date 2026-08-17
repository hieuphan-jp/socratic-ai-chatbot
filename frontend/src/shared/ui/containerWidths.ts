/**
 * shared/ui/containerWidths.ts
 *
 * JA: `PageContainer`(本文)と`PageHeader`(見出しバー)は別々のコンポーネントだが、
 *     中身の横幅は必ず揃える必要がある(揃わないと見出しと本文の左右位置がズレる)。
 *     2箇所に同じ表を書くと片方だけ直して食い違う事故が起きるため、ここに1つだけ置く。
 * VI: `PageContainer` (nội dung) và `PageHeader` (thanh tiêu đề) là 2 component riêng,
 *     nhưng chiều rộng nội dung bắt buộc phải khớp nhau (không khớp thì tiêu đề và nội
 *     dung sẽ lệch trái/phải). Viết bảng này ở 2 nơi dễ gây lệch khi chỉ sửa 1 chỗ, nên
 *     chỉ đặt đúng 1 nơi duy nhất.
 */
export type ContainerWidth = 'narrow' | 'normal' | 'wide'

export const CONTAINER_WIDTHS: Record<ContainerWidth, string> = {
  narrow: 'max-w-md',
  normal: 'max-w-4xl',
  wide: 'max-w-7xl',
}
