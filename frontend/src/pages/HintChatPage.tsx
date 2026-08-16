/**
 * pages/HintChatPage.tsx
 *
 * JA: ヒントチャット画面。組み立てのみ行い、中身は features/hintChat に置く。
 *     ★URLに :sessionId があれば、そのセッションを開いた状態で始める(学習木の葉から
 *     「復習を始める」で入ってくる経路)。無ければ従来通り新規チャットとして始まる。
 *     セッションが変わったらkeyで再マウントし、前のセッションの入力欄や思考ツリーの
 *     状態が残らないようにする。
 * VI: Trang chat hint. Chỉ lắp ghép, nội dung nằm ở features/hintChat.
 *     ★Nếu URL có :sessionId thì mở sẵn phiên đó (đường vào từ nút "Bắt đầu ôn tập"
 *     ở lá cây học tập). Không có thì bắt đầu như một phiên chat mới như trước.
 *     Khi đổi phiên thì remount qua key để state ô nhập/cây tư duy của phiên cũ không sót lại.
 */
import { Link, useParams } from 'react-router-dom'

import { HintChatView } from '@/features/hintChat/components/HintChatView'

export function HintChatPage() {
  const { sessionId } = useParams<{ sessionId?: string }>()

  return (
    <main style={{ maxWidth: '1200px', width: '100%', margin: '20px auto', padding: '0 20px', display: 'grid', gap: 20, boxSizing: 'border-box' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 20, fontWeight: 'bold' }}>ヒントチャット / Chat gợi ý</h1>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <Link to="/learning-tree" style={{ color: '#4f46e5', textDecoration: 'underline' }}>
            学習内容ツリー / Cây nội dung
          </Link>
          <Link to="/" style={{ color: '#4f46e5', textDecoration: 'underline' }}>戻る / Quay lại</Link>
        </div>
      </header>
      <HintChatView key={sessionId ?? 'new'} activeSessionId={sessionId} />
    </main>
  )
}
