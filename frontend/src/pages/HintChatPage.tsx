/**
 * pages/HintChatPage.tsx
 *
 * JA: ヒントチャット画面。組み立てのみ行い、中身は features/hintChat に置く。
 * VI: Trang chat hint. Chỉ lắp ghép, nội dung nằm ở features/hintChat.
 */
import { Link } from 'react-router-dom'

import { HintChatView } from '@/features/hintChat/components/HintChatView'

export function HintChatPage() {
  return (
    <main style={{ maxWidth: '1200px', width: '100%', margin: '20px auto', padding: '0 20px', display: 'grid', gap: 20, boxSizing: 'border-box' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 20, fontWeight: 'bold' }}>ヒントチャット / Chat gợi ý</h1>
        <Link to="/" style={{ color: '#4f46e5', textDecoration: 'underline' }}>戻る / Quay lại</Link>
      </header>
      <HintChatView />
    </main>
  )
}