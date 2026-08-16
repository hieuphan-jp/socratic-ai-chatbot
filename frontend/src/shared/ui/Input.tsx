/**
 * shared/ui/Input.tsx
 *
 * JA: 1行入力。検索欄のように左にアイコンを置きたい場合は icon を渡す。
 *     ★preflight を切っているため、ブラウザ既定の枠線・フォントを明示的に指定している。
 * VI: Ô nhập 1 dòng. Muốn đặt icon bên trái (như ô tìm kiếm) thì truyền icon.
 *     ★Vì đã tắt preflight, phải chỉ định rõ viền/font thay cho mặc định trình duyệt.
 */
import type { InputHTMLAttributes, ReactNode } from 'react'

import { cn } from '@/shared/lib/cn'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  /** JA: 左端に置く小さなアイコン(lucide-react) / VI: Icon nhỏ đặt ở mép trái (lucide-react) */
  icon?: ReactNode
}

export function Input({ icon, className, ...rest }: InputProps) {
  const field = (
    <input
      {...rest}
      className={cn(
        'w-full rounded-2xl border border-slate-200 bg-white py-2.5 text-sm text-slate-700',
        'placeholder:text-slate-400',
        'focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100',
        'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400',
        icon ? 'pl-10 pr-4' : 'px-4',
        className
      )}
    />
  )

  if (!icon) return field

  return (
    <div className="relative w-full">
      <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
        {icon}
      </span>
      {field}
    </div>
  )
}
