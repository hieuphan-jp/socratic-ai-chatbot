/**
 * shared/ui/Button.tsx
 *
 * JA: アプリ共通のボタン。役割(variant)と大きさ(size)だけを選ばせ、色や角丸は
 *     ここで固定する。画面側で bg-* や rounded-* を上書きしないこと
 *     (上書きしたくなったら、それは新しい variant が必要というサイン)。
 *     ★preflight(全体リセット)を切っているため、ブラウザ既定の枠線・背景・フォントを
 *     明示的に打ち消している(border-0 / bg-transparent は消さないこと)。
 * VI: Nút dùng chung toàn app. Chỉ cho chọn vai trò (variant) và kích thước (size);
 *     màu và bo góc cố định ở đây. Phía màn hình KHÔNG ghi đè bg-* hay rounded-*
 *     (muốn ghi đè nghĩa là cần thêm một variant mới).
 *     ★Vì đã tắt preflight (reset toàn cục), phải chủ động khử viền/nền/font mặc định
 *     của trình duyệt (đừng xóa border-0 / bg-transparent).
 */
import type { ButtonHTMLAttributes } from 'react'

import { cn } from '@/shared/lib/cn'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md'

const VARIANTS: Record<ButtonVariant, string> = {
  // JA: 画面で一番やってほしい操作。1画面に1つが目安。
  // VI: Hành động muốn user làm nhất trên màn hình. Mỗi màn hình nên chỉ 1 cái.
  primary: 'border-0 bg-teal-600 text-white hover:bg-teal-700 disabled:bg-slate-300',
  // JA: 並列の選択肢・補助操作。
  // VI: Lựa chọn ngang hàng, thao tác phụ.
  secondary:
    'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:text-slate-300',
  // JA: 枠を出したくない軽い操作(閉じる・切替など)。
  // VI: Thao tác nhẹ, không muốn có khung (đóng, chuyển đổi...).
  ghost:
    'border-0 bg-transparent text-slate-500 hover:bg-slate-100 hover:text-slate-700 disabled:text-slate-300',
  // JA: 取り消せない操作(削除など)。今は使い所が無いが、赤を各自が自作しないよう先に定義する。
  // VI: Thao tác không hoàn tác được (xóa...). Hiện chưa dùng, định nghĩa sẵn để không ai tự chế màu đỏ.
  danger: 'border-0 bg-rose-600 text-white hover:bg-rose-700 disabled:bg-slate-300',
}

const SIZES: Record<ButtonSize, string> = {
  sm: 'gap-1.5 px-3 py-1.5 text-xs',
  md: 'gap-2 px-4 py-2.5 text-sm',
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  size?: ButtonSize
  /** JA: 横幅いっぱいに広げる / VI: Kéo rộng hết chiều ngang */
  block?: boolean
}

export function Button({
  variant = 'secondary',
  size = 'md',
  block = false,
  className,
  type = 'button',
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      type={type}
      className={cn(
        'inline-flex items-center justify-center rounded-2xl font-medium transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-500',
        'disabled:cursor-not-allowed',
        VARIANTS[variant],
        SIZES[size],
        block && 'w-full',
        className
      )}
    />
  )
}
