/**
 * shared/ui/Card.tsx
 *
 * JA: 情報のまとまりを表す面(サーフェス)。角丸・枠線・影をここに固定し、
 *     画面側では tone(色の意味)だけを選ぶ。
 *     tone の使い分け:
 *       default = ふつうの情報 / accent = 前向きな結果(定着など)
 *       attention = 今やるべきこと(復習期限など) / muted = 補足・控えめな箱
 * VI: Mặt (surface) biểu thị một khối thông tin. Bo góc/viền/đổ bóng cố định ở đây,
 *     phía màn hình chỉ chọn tone (ý nghĩa màu).
 *     Cách dùng tone:
 *       default = thông tin thường / accent = kết quả tích cực (đã ghi nhớ...)
 *       attention = việc cần làm ngay (tới hạn ôn...) / muted = phần bổ sung, nhẹ nhàng
 */
import type { HTMLAttributes } from 'react'

import { cn } from '@/shared/lib/cn'

export type CardTone = 'default' | 'accent' | 'attention' | 'muted'

const TONES: Record<CardTone, string> = {
  default: 'border-slate-100 bg-white shadow-sm',
  accent: 'border-emerald-100 bg-emerald-50/60',
  attention: 'border-amber-100 bg-amber-50/50',
  muted: 'border-slate-100 bg-slate-50/70',
}

type CardProps = HTMLAttributes<HTMLDivElement> & {
  tone?: CardTone
  /** JA: 内側の余白を自分で決めたい時は false / VI: Đặt false nếu muốn tự quyết padding bên trong */
  padded?: boolean
}

export function Card({ tone = 'default', padded = true, className, ...rest }: CardProps) {
  return (
    <div
      {...rest}
      className={cn('rounded-3xl border', TONES[tone], padded && 'p-5', className)}
    />
  )
}
