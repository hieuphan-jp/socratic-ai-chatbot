/**
 * shared/ui/SegmentedControl.tsx
 *
 * JA: 2〜3個の排他的な表示切替(「木構造/タイムログ」「詳細/会話ログ」など)。
 *     既に2箇所で同じものを手書きしていたので共通化した。
 *     ★選択肢が4つ以上・階層があるならタブではなく別の設計を検討すること。
 * VI: Chuyển đổi hiển thị loại trừ nhau, 2-3 mục ("Cây/Nhật ký", "Chi tiết/Lịch sử"...).
 *     Đã có 2 chỗ tự viết trùng nhau nên gom lại thành component chung.
 *     ★Nếu có từ 4 lựa chọn trở lên hoặc có phân cấp thì nên cân nhắc thiết kế khác, không dùng tab.
 */
import type { ReactNode } from 'react'

import { cn } from '@/shared/lib/cn'

export type SegmentedOption<T extends string> = {
  value: T
  label: string
  icon?: ReactNode
}

type SegmentedControlProps<T extends string> = {
  options: ReadonlyArray<SegmentedOption<T>>
  value: T
  onChange: (value: T) => void
  /** JA: アクセシビリティ用のグループ名 / VI: Tên nhóm cho accessibility */
  ariaLabel: string
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className="inline-flex rounded-2xl border border-slate-200 bg-white p-1 shadow-sm"
    >
      {options.map((option) => {
        const selected = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(option.value)}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-xl border-0 px-4 py-1.5 text-sm font-medium transition-colors',
              'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-500',
              // ★teal-700。白文字コントラストがWCAG AA未達(3.66:1)だったteal-600から変更(Button.tsx参照)。
              // ★teal-700. Đổi từ teal-600 vì tương phản chữ trắng không đạt WCAG AA (3.66:1) (xem Button.tsx).
              selected
                ? 'bg-teal-700 text-white'
                : 'bg-transparent text-slate-500 hover:text-slate-700'
            )}
          >
            {option.icon}
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
