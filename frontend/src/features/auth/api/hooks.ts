/**
 * features/auth/api/hooks.ts
 *
 * JA: 認証のサーバ状態を扱う TanStack Query フック。通信は必ず shared/api の api 経由。
 *     - useMe():     現在ユーザー取得（未ログインなら 401 → client がログイン画面へ誘導）
 *     - useLogin():  ログイン。成功したら me を無効化して再取得させる
 *     - useLogout(): ログアウト。キャッシュを消す
 *     ★fetch を直接呼ばない／クエリキーは shared/api/queryKeys から取る、が厳守事項。
 * VI: Hook TanStack Query xử lý trạng thái xác thực từ server. Giao tiếp luôn qua api của shared/api.
 *     - useMe():     lấy user hiện tại (chưa đăng nhập -> 401 -> client đưa về trang login)
 *     - useLogin():  đăng nhập; thành công thì invalidate me để lấy lại
 *     - useLogout(): đăng xuất; xóa cache
 *     ★Không gọi fetch trực tiếp / lấy query key từ shared/api/queryKeys là bắt buộc.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { User } from '@/shared/types'

type Credentials = { username: string; password: string }

export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => api.get<User>('/auth/me/'),
    // JA: 認証状態は頻繁に変わらないので軽めに。失敗時のリトライはしない（401を素早く扱う）。
    // VI: Trạng thái auth ít đổi nên nhẹ. Không retry khi lỗi (xử lý 401 nhanh).
    retry: false,
    staleTime: 60_000,
  })
}

export function useLogin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (creds: Credentials) => api.post<User>('/auth/login/', creds),
    onSuccess: (user) => {
      // JA: 取得済みの me を即差し替え、関連クエリを無効化する。
      // VI: Thay ngay me đã có và invalidate các query liên quan.
      qc.setQueryData(queryKeys.me, user)
      qc.invalidateQueries({ queryKey: queryKeys.me })
    },
  })
}

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<void>('/auth/logout/'),
    onSuccess: () => {
      // JA: ログアウト後は全キャッシュを捨てて他人のデータ残存を防ぐ。
      // VI: Sau khi đăng xuất, xóa toàn bộ cache để tránh sót dữ liệu người khác.
      qc.clear()
    },
  })
}

// JA: CSRF Cookie を事前取得するための一回きりの呼び出し（アプリ起動時に使う）。
// VI: Gọi một lần để lấy trước CSRF Cookie (dùng khi khởi động app).
export function fetchCsrf() {
  return api.get<{ csrfToken: string }>('/auth/csrf/')
}
