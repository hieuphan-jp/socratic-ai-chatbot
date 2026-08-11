/**
 * app/App.tsx
 *
 * JA: アプリのルート。Provider でルーターを包むだけ。起動時に CSRF Cookie を先読みして、
 *     最初の POST（ログイン）でトークンが確実に付くようにする。
 * VI: Gốc của app. Chỉ bọc router bằng Provider. Khi khởi động, nạp trước CSRF Cookie để
 *     POST đầu tiên (đăng nhập) chắc chắn có token.
 */
import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'

import { fetchCsrf } from '@/features/auth/api/hooks'

import { AppProviders } from './providers'
import { router } from './router'

export function App() {
  useEffect(() => {
    // JA: 失敗しても致命的でないので握りつぶす（後続の CSRF 取得でも間に合う）。
    // VI: Lỗi cũng không nghiêm trọng nên bỏ qua (lần lấy CSRF sau vẫn kịp).
    void fetchCsrf().catch(() => {})
  }, [])

  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  )
}