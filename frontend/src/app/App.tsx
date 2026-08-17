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
    // JA: あくまで先読み(最初のPOSTを速くするだけ)。失敗しても致命的ではない。
    //     ここが失敗しても、変更系リクエストの直前に client.ts が改めてトークンを
    //     取り寄せるため、CSRFが空のまま詰まることはない。
    // VI: Chỉ là nạp trước (để POST đầu tiên nhanh hơn), lỗi cũng không nghiêm trọng.
    //     Kể cả lỗi ở đây, client.ts vẫn tự lấy lại token ngay trước request thay đổi
    //     dữ liệu, nên không bị kẹt với CSRF rỗng.
    void fetchCsrf().catch(() => {})
  }, [])

  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  )
}