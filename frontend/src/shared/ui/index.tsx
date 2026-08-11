/**
 * shared/ui/index.tsx
 *
 * JA: 全 feature で使い回す最小限の共通 UI 部品。見た目の統一とマークアップの重複排除が目的。
 *     ここには「どの機能にも依存しない」汎用部品だけを置く（業務ロジックを持ち込まない）。
 * VI: Bộ UI dùng chung tối thiểu cho mọi feature. Mục đích: đồng nhất giao diện, tránh lặp markup.
 *     Chỉ đặt component tổng quát "không phụ thuộc feature nào" (không mang logic nghiệp vụ).
 */
import type { ButtonHTMLAttributes, InputHTMLAttributes } from 'react'

export function Button(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  const { style, ...rest } = props
  return (
    <button
      {...rest}
      style={{
        padding: '8px 14px',
        borderRadius: 6,
        border: '1px solid #ccc',
        cursor: props.disabled ? 'not-allowed' : 'pointer',
        ...style,
      }}
    />
  )
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  const { style, ...rest } = props
  return (
    <input
      {...rest}
      style={{ padding: '8px 10px', borderRadius: 6, border: '1px solid #ccc', ...style }}
    />
  )
}

// JA: エラー・空・読み込みの表示を統一する小物。
// VI: Tiện ích nhỏ để hiển thị lỗi/rỗng/đang tải một cách nhất quán.
export function Notice({ children }: { children: React.ReactNode }) {
  return <p style={{ color: '#666', fontSize: 14 }}>{children}</p>
}

export function ErrorText({ children }: { children: React.ReactNode }) {
  return <p style={{ color: '#c0392b', fontSize: 14 }}>{children}</p>
}
