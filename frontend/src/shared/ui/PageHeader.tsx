/**
 * shared/ui/PageHeader.tsx
 *
 * JA: 各ページの先頭に置く見出し。全画面で同じ形にするための部品。
 *     ★多言語化により「日本語 / ベトナム語」の併記は不要になったため、subtitle は
 *     翻訳の置き場ではなく「その画面が何をする所か」の一言説明として使う。
 *     ★2026-08 見直し: 四方を枠線で囲んだ「カード」ではなく、画面の横幅いっぱいに
 *     伸びるバーにした。区切りは下線1本だけ(border-b)。中身(タイトル等)だけを
 *     `width` で本文(PageContainer)と同じ最大幅に揃えるので、見出しと本文の
 *     左右位置は自動で揃う。`PageContainer` の外側・直前に置いて使う。
 * VI: Tiêu đề đặt ở đầu mỗi trang. Component để mọi màn hình có cùng một hình thức.
 *     ★Nhờ đa ngôn ngữ, không cần ghi kèm "tiếng Nhật / tiếng Việt" nữa; subtitle
 *     dùng làm câu mô tả ngắn "màn hình này để làm gì", không phải chỗ chứa bản dịch.
 *     ★Sửa lại 08/2026: không còn là "card" viền 4 cạnh, mà là thanh dài hết chiều
 *     rộng màn hình. Chỉ có 1 đường viền dưới (border-b) làm ranh giới. Chỉ phần nội
 *     dung (tiêu đề...) được giới hạn theo `width`, khớp với `PageContainer` nên tiêu
 *     đề và nội dung tự động thẳng hàng. Đặt ngay trước `PageContainer`, ở ngoài nó.
 */
import type { ReactNode } from 'react'

import { cn } from '@/shared/lib/cn'
import { CONTAINER_WIDTHS } from './containerWidths'
import type { ContainerWidth } from './containerWidths'

type PageHeaderProps = {
  title: string
  subtitle?: string
  /** JA: 右端に置く操作(戻るリンク・言語切替など) / VI: Thao tác đặt ở mép phải (link quay lại, đổi ngôn ngữ...) */
  actions?: ReactNode
  /** JA: 同じ画面の PageContainer と同じ値を渡すこと(位置を揃えるため) / VI: Truyền cùng giá trị với PageContainer của màn hình đó (để thẳng hàng) */
  width?: ContainerWidth
  className?: string
}

export function PageHeader({ title, subtitle, actions, width = 'normal', className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'w-full border-b border-slate-100 bg-gradient-to-r from-teal-50/60 via-indigo-50/40 to-slate-50',
        className
      )}
    >
      <div
        className={cn(
          'mx-auto flex items-center justify-between gap-4 px-4 py-5 sm:px-6',
          CONTAINER_WIDTHS[width]
        )}
      >
        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold text-slate-800">{title}</h1>
          {subtitle && <p className="mt-0.5 truncate text-xs text-slate-500">{subtitle}</p>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
      </div>
    </div>
  )
}
