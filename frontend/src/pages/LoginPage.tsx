/**
 * pages/LoginPage.tsx
 *
 * JA: ログイン画面。pages は「組み立て」だけを担う（部品を並べ、遷移を指示するのみ）。
 *     ログインの中身は features/auth の LoginForm、遷移は router に任せる。
 * VI: Trang đăng nhập. pages chỉ lo "lắp ghép" (đặt component, chỉ định điều hướng).
 *     Nội dung đăng nhập giao cho LoginForm của features/auth, điều hướng giao cho router.
 */
import { useNavigate } from 'react-router-dom'

import { LoginForm } from '@/features/auth/components/LoginForm'

export function LoginPage() {
  const navigate = useNavigate()
  return (
    <main style={{ maxWidth: 320, margin: '80px auto', display: 'grid', gap: 16 }}>
      <h1 style={{ fontSize: 20 }}>ログイン / Đăng nhập</h1>
      {/* JA: 成功したらトップへ / VI: Thành công thì về trang chủ */}
      <LoginForm onSuccess={() => navigate('/')} />
    </main>
  )
}
