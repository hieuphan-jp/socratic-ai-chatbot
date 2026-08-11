/**
 * app/router.tsx
 *
 * JA: ルート定義。どの URL がどの page を出すかだけを宣言する（組み立ては page 側）。
 *     保護ルートは RequireAuth で包む。新しい画面は page を作ってここに1行足す。
 * VI: Định nghĩa route. Chỉ khai báo URL nào hiển thị page nào (lắp ghép ở page).
 *     Route cần bảo vệ bọc bằng RequireAuth. Màn hình mới: tạo page rồi thêm 1 dòng ở đây.
 */
import { createBrowserRouter, Navigate } from 'react-router-dom'

import { HintChatPage } from '@/pages/HintChatPage'
import { HomePage } from '@/pages/HomePage'
import { LearningTreePage } from '@/pages/LearningTreePage'
import { LoginPage } from '@/pages/LoginPage'

import { RequireAuth } from './RequireAuth'

export const router = createBrowserRouter([
  // JA: 保護されたトップ（ログイン後の着地点）。VI: Trang chủ được bảo vệ (điểm đến sau đăng nhập).
  {
    path: '/',
    element: (
      <RequireAuth>
        <HomePage />
      </RequireAuth>
    ),
  },
  {
    path: '/learning-tree',
    element: (
      <RequireAuth>
        <LearningTreePage />
      </RequireAuth>
    ),
  },
  {
    path: '/hint-chat',
    element: (
      <RequireAuth>
        <HintChatPage />
      </RequireAuth>
    ),
  },
  { path: '/login', element: <LoginPage /> },
  // JA: 未知のパスはトップへ。VI: Đường dẫn lạ về trang chủ.
  { path: '*', element: <Navigate to="/" replace /> },
])
