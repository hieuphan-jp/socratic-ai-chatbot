/**
 * shared/ui/PageHeader.tsx
 *
 * JA: 各ページの先頭に置く見出し。全画面で同じ形にするための部品。
 *     ★多言語化により「日本語 / ベトナム語」の併記は不要になったため、subtitle は
 *     翻訳の置き場ではなく「その画面が何をする所か」の一言説明として使う。
 * VI: Tiêu đề đặt ở đầu mỗi trang. Component để mọi màn hình có cùng một hình thức.
 *     ★Nhờ đa ngôn ngữ, không cần ghi kèm "tiếng Nhật / tiếng Việt" nữa; subtitle
 *     dùng làm câu mô tả ngắn "màn hình này để làm gì", không phải chỗ chứa bản dịch.
 */
import type { ReactNode } from 'react'

import { cn } from '@/shared/lib/cn'

type PageHeaderProps = {
  title: string
  subtitle?: string
  /** JA: 右端に置く操作(戻るリンク・言語切替など) / VI: Thao tác đặt ở mép phải (link quay lại, đổi ngôn ngữ...) */
  actions?: ReactNode
  className?: string
}

export function PageHeader({ title, subtitle, actions, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between gap-4 rounded-3xl border border-slate-100',
        'bg-gradient-to-r from-teal-50/60 via-indigo-50/40 to-slate-50 px-6 py-5',
        className
      )}
    >
      <div className="min-w-0">
        <h1 className="truncate text-lg font-semibold text-slate-800">{title}</h1>
        {subtitle && <p className="mt-0.5 truncate text-xs text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}
