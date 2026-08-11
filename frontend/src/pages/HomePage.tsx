/**
 * pages/HomePage.tsx
 *
 * JA: ログイン後の着地点となる最小の土台ページ（プレースホルダ）。
 *     認証の動作確認用に、現在ユーザー表示とログアウトだけを置く。機能の中身は各担当が
 *     features/ を作り、pages/ と app/router.tsx に追加していく（手順は CONVENTIONS.md §5）。
 * VI: Trang nền tối thiểu làm điểm đến sau khi đăng nhập (placeholder).
 *     Chỉ hiển thị user hiện tại và nút đăng xuất để kiểm tra xác thực. Nội dung tính năng do
 *     mỗi người tạo trong features/ rồi thêm vào pages/ và app/router.tsx (xem CONVENTIONS.md §5).
 */
import { useNavigate } from 'react-router-dom'

import { useLogout, useMe } from '@/features/auth/api/hooks'
import { Button, Notice } from '@/shared/ui'

export function HomePage() {
  const navigate = useNavigate()
  const me = useMe()
  const logout = useLogout()

  return (
    <main style={{ maxWidth: 560, margin: '40px auto', display: 'grid', gap: 20 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 20 }}>ホーム / Trang chủ</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {me.data && <span style={{ fontSize: 14, color: '#666' }}>{me.data.username}</span>}
          <Button onClick={() => logout.mutate(undefined, { onSuccess: () => navigate('/login') })}>
            ログアウト / Đăng xuất
          </Button>
        </div>
      </header>
      {/* JA: ここから各機能を追加する / VI: Thêm các tính năng từ đây */}
      <Notice>
        ここに各自の機能を追加します（features/ を作成 → pages/ で組み立て → router に追加）。
        / Thêm tính năng của bạn tại đây (tạo features/ → lắp ở pages/ → thêm vào router).
      </Notice>
    </main>
  )
}
