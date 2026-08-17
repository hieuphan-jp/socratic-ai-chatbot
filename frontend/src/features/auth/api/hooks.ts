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

import { api, setCsrfToken } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { User } from '@/shared/types'

type Credentials = { username: string; password: string }

// JA: ★ログイン/新規登録のレスポンス本文には、ユーザー情報に加えて最新のcsrfToken
//     も乗っている(apps/accounts/views.py参照)。login()はサーバー側でCSRFトークンを
//     ローテーションするため、以前(/auth/csrf/取得時)のトークンはここで失効している。
// VI: ★Body response của đăng nhập/đăng ký, ngoài thông tin user còn kèm csrfToken
//     mới nhất (xem apps/accounts/views.py). Vì login() ở server rotate CSRF token,
//     token lấy từ trước (/auth/csrf/) đã hết hiệu lực tại đây.
type AuthResponse = User & { csrfToken: string }

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
    mutationFn: (creds: Credentials) => api.post<AuthResponse>('/auth/login/', creds),
    onSuccess: ({ csrfToken, ...user }) => {
      // JA: ローテーションされた最新のCSRFトークンを反映してから、
      //     取得済みの me を即差し替え、関連クエリを無効化する。
      // VI: Cập nhật CSRF token mới nhất (đã rotate) trước, rồi thay ngay
      //     me đã có và invalidate các query liên quan.
      setCsrfToken(csrfToken)
      qc.setQueryData(queryKeys.me, user)
      qc.invalidateQueries({ queryKey: queryKeys.me })
    },
  })
}

// JA: ★新規登録。発表デモでの同時利用向け(demo/demo12345の単一共有アカウントだと
//     参加者全員のデータが混ざるため、各自がここで自分のアカウントを作れるようにした)。
//     成功したらバックエンド側で即ログイン状態になるので、useLoginと同じくmeを差し替える。
// VI: ★Đăng ký mới. Dùng cho việc nhiều người dùng đồng thời khi demo thuyết trình
//     (tài khoản demo/demo12345 dùng chung sẽ làm dữ liệu mọi người trộn lẫn, nên cho
//     mỗi người tự tạo tài khoản riêng ở đây). Thành công thì backend đã tự đăng nhập
//     luôn, nên cũng thay me giống useLogin.
export function useSignup() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (creds: Credentials) => api.post<AuthResponse>('/auth/signup/', creds),
    onSuccess: ({ csrfToken, ...user }) => {
      // JA: useLoginと同じ理由でCSRFトークンを先に反映する。
      // VI: Cập nhật CSRF token trước, cùng lý do với useLogin.
      setCsrfToken(csrfToken)
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
      // JA: ★保持しているCSRFトークンも必ず捨てる。Djangoのlogout()はサーバー側で
      //     CSRFトークンをローテーションするため、ログアウト前のトークンは即座に
      //     失効する。ここで捨てないと、client.tsのensureCsrfTokenが「トークンは
      //     ある」と判断して再取得をスキップし、古いトークンを送り続けて、
      //     ログインし直した後の変更系リクエストが全て403になる
      //     (実際に本番で「ログアウトして入り直すと403」として発生した)。
      //     空にしておけば、次の変更系リクエストの直前に新しいトークンを取り直す。
      // VI: ★Bắt buộc xóa cả CSRF token đang giữ. logout() của Django rotate CSRF
      //     token ở phía server, nên token trước khi đăng xuất mất hiệu lực ngay.
      //     Không xóa ở đây thì ensureCsrfToken trong client.ts sẽ tưởng "đã có token"
      //     và bỏ qua việc lấy lại, cứ gửi token cũ, khiến mọi request thay đổi dữ
      //     liệu sau khi đăng nhập lại đều bị 403 (đã xảy ra thật ở production với
      //     hiện tượng "đăng xuất rồi vào lại thì bị 403"). Để rỗng thì lần request
      //     thay đổi dữ liệu kế tiếp sẽ tự lấy token mới.
      setCsrfToken('')
      // JA: ログアウト後は全キャッシュを捨てて他人のデータ残存を防ぐ。
      // VI: Sau khi đăng xuất, xóa toàn bộ cache để tránh sót dữ liệu người khác.
      qc.clear()
    },
  })
}

// JA: CSRFトークンを事前取得するための一回きりの呼び出し（アプリ起動時に使う）。
//     ★取得したトークンを必ずclient.tsのメモリに反映する。以前はここで
//     レスポンスを受け取るだけで値を使っていなかったため、実質何もしていない
//     呼び出しになっていた(readCsrfTokenがdocument.cookieを直接読んでいたため)。
// VI: Gọi một lần để lấy trước CSRF token (dùng khi khởi động app).
//     ★Bắt buộc phản ánh token lấy được vào bộ nhớ ở client.ts. Trước đây chỉ
//     nhận response mà không dùng giá trị (vì readCsrfToken đọc thẳng
//     document.cookie), nên lệnh gọi này thực chất không có tác dụng gì.
export async function fetchCsrf() {
  const { csrfToken } = await api.get<{ csrfToken: string }>('/auth/csrf/')
  setCsrfToken(csrfToken)
}
