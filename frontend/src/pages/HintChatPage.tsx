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
    <main style={{ maxWidth: 560, margin: '40px auto', display: 'grid', gap: 20 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 20 }}>ヒントチャット / Chat gợi ý</h1>
        <Link to="/">戻る / Quay lại</Link>
      </header>
      <HintChatView />
    </main>
  )
}
