/**
 * shared/ui/Feedback.tsx
 *
 * JA: 「読み込み中 / エラー / 空 / 補足」の4状態の表示を1箇所に集める。
 *     ★CONVENTIONS.md §9.2 の通り、一覧系の画面は必ずこの4状態を出し分けること。
 *     各画面がバラバラの文言・色で書くと、同じ状態なのに見え方が変わってしまう。
 * VI: Gom hiển thị 4 trạng thái "đang tải / lỗi / rỗng / ghi chú" về một chỗ.
 *     ★Theo CONVENTIONS.md §9.2, màn hình dạng danh sách BẮT BUỘC phân biệt đủ 4 trạng thái này.
 *     Nếu mỗi màn tự viết chữ và màu riêng thì cùng một trạng thái lại trông khác nhau.
 */
import type { ReactNode } from 'react'

import { cn } from '@/shared/lib/cn'

/** JA: 補足・注記(本文より弱い情報) / VI: Ghi chú, bổ sung (thông tin yếu hơn body) */
export function Notice({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn('text-sm text-slate-500', className)}>{children}</p>
}

/** JA: エラー(操作が失敗したこと) / VI: Lỗi (thao tác đã thất bại) */
export function ErrorText({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn('text-sm text-rose-600', className)}>{children}</p>
}

/** JA: 読み込み中 / VI: Đang tải */
export function LoadingText({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn('text-sm text-slate-400', className)}>{children}</p>
}

/**
 * JA: 空状態。「無い」ことを責めずに、次の一歩を示せる時は action を渡す。
 * VI: Trạng thái rỗng. Đừng trách user vì "không có gì"; nếu gợi ý được bước tiếp theo thì truyền action.
 */
export function EmptyState({
  icon,
  message,
  action,
  className,
}: {
  icon?: ReactNode
  message: string
  action?: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center gap-3 rounded-2xl bg-slate-50/70 px-6 py-8 text-center',
        className
      )}
    >
      {icon && <span className="text-slate-300">{icon}</span>}
      <p className="text-sm text-slate-500">{message}</p>
      {action}
    </div>
  )
}
