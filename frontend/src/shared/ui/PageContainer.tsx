/**
 * shared/ui/PageContainer.tsx
 *
 * JA: ページ全体の外枠。最大幅・左右の余白・縦のリズム(要素間の間隔)を1箇所に固定し、
 *     どの画面を開いても中身の始まる位置が揃うようにする。
 *     width は画面の性質で選ぶ:
 *       narrow = 読む/入力する画面(ログイン等) / normal = 一覧・詳細の標準
 *       wide   = 横に広い作業画面(チャット+思考ツリーのように2カラム必要なもの)
 * VI: Khung ngoài của cả trang. Cố định chiều rộng tối đa, lề trái/phải và nhịp dọc
 *     (khoảng cách giữa các khối) ở một chỗ, để mở màn nào thì nội dung cũng bắt đầu ở cùng vị trí.
 *     Chọn width theo tính chất màn hình:
 *       narrow = màn để đọc/nhập (đăng nhập...) / normal = mặc định cho danh sách, chi tiết
 *       wide   = màn làm việc rộng ngang (cần 2 cột như chat + cây tư duy)
 */
import type { ReactNode } from 'react'

import { cn } from '@/shared/lib/cn'
import { CONTAINER_WIDTHS } from './containerWidths'
import type { ContainerWidth } from './containerWidths'

export function PageContainer({
  width = 'normal',
  children,
  className,
}: {
  width?: ContainerWidth
  children: ReactNode
  className?: string
}) {
  return (
    <main className={cn('mx-auto space-y-6 p-4 sm:p-6', CONTAINER_WIDTHS[width], className)}>
      {children}
    </main>
  )
}
