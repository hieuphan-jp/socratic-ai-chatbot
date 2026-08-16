/**
 * shared/ui/Badge.tsx
 *
 * JA: 状態を1語で示す小さな丸ピル。件数・「復習」「本日」などに使う。
 *     ★本文より目立たせないため、必ず本文より小さい文字サイズで固定している。
 * VI: Pill tròn nhỏ, thể hiện trạng thái bằng 1 từ. Dùng cho số lượng, "Ôn tập", "Hôm nay"...
 *     ★Để không nổi hơn nội dung chính, cỡ chữ luôn nhỏ hơn body và cố định ở đây.
 */
import type { HTMLAttributes } from 'react'

import { cn } from '@/shared/lib/cn'

export type BadgeTone = 'neutral' | 'accent' | 'attention' | 'brand'

const TONES: Record<BadgeTone, string> = {
  neutral: 'bg-slate-100 text-slate-600',
  accent: 'bg-emerald-100 text-emerald-700',
  attention: 'bg-amber-100 text-amber-700',
  brand: 'bg-teal-100 text-teal-700',
}

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: BadgeTone
}

export function Badge({ tone = 'neutral', className, ...rest }: BadgeProps) {
  return (
    <span
      {...rest}
      className={cn(
        'inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium',
        TONES[tone],
        className
      )}
    />
  )
}
