/**
 * shared/api/client.ts
 *
 * JA: ★全HTTP通信の唯一の入口。features や pages は fetch を直接呼ばず、必ずここを通す。
 *     ここに一極集中させる責務:
 *       - Cookie を送る（credentials: 'include'）＝セッション認証の前提
 *       - 変更系(POST/PUT/PATCH/DELETE)に CSRF トークンを自動付与
 *       - 401 のときログイン画面へリダイレクト
 *       - エラーを ApiError に整形（画面は一貫した形で扱える）
 *     こうすると認証・CSRF・エラー処理の方針が1ファイルに揃い、5人の実装がブレない。
 * VI: ★Cửa duy nhất cho MỌI giao tiếp HTTP. features/pages KHÔNG gọi fetch trực tiếp mà luôn qua đây.
 *     Trách nhiệm gom về một chỗ:
 *       - Gửi Cookie (credentials: 'include') = tiền đề của session auth
 *       - Tự gắn CSRF token cho method thay đổi dữ liệu (POST/PUT/PATCH/DELETE)
 *       - Khi 401 thì chuyển hướng về trang đăng nhập
 *       - Chuẩn hóa lỗi thành ApiError (màn hình xử lý nhất quán)
 *     Nhờ vậy chính sách auth/CSRF/xử lý lỗi gom trong 1 file, 5 người không lệch nhau.
 */
import { DEFAULT_LOCALE, loadLocale } from '@/shared/i18n/locale'
import { messages } from '@/shared/i18n/messages'

// JA: API の基点。ローカル開発は Vite プロキシ経由なので相対パス '/api' のままでよいが、
//     本番はフロントとバックエンドが別ドメインなので相対パスだとフロント自身のドメインを
//     叩いてしまう。VITE_API_BASE_URL(例: https://xxx.onrender.com/api)があればそちらを使う。
// VI: Gốc API. Local dev đi qua proxy Vite nên đường dẫn tương đối '/api' vẫn ổn, nhưng ở
//     production frontend/backend khác domain nên đường dẫn tương đối sẽ gọi nhầm vào chính
//     domain của frontend. Nếu có VITE_API_BASE_URL (vd: https://xxx.onrender.com/api) thì dùng nó.
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

// JA: ★このファイルはReactの外(コンポーネント無し)で動くため useI18n() は使えない。
//     messages 辞書と loadLocale を直接読む純粋関数呼び出しで多言語化する
//     (サーバが detail を返さなかった時の通信エラーの既定文言のみが対象)。
// VI: ★File này chạy ngoài React (không có component) nên không dùng được useI18n().
//     Đa ngôn ngữ hóa bằng cách gọi trực tiếp hàm thuần đọc từ điển messages và
//     loadLocale (chỉ áp dụng cho câu chữ lỗi mặc định khi server không trả detail).
function requestFailedMessage(status: number): string {
  const locale = loadLocale()
  const table = messages[locale] ?? messages[DEFAULT_LOCALE]
  const template = table['common.requestFailed'] ?? messages[DEFAULT_LOCALE]['common.requestFailed']
  return template.replace('{status}', String(status))
}

// JA: ログイン画面のパス。401 時のリダイレクト先。router と一致させること。
// VI: Đường dẫn trang đăng nhập, đích chuyển hướng khi 401. Phải khớp với router.
const LOGIN_PATH = '/login'

/**
 * JA: 画面へ渡す統一エラー型。status とサーバのメッセージを持つ。
 * VI: Kiểu lỗi thống nhất đưa lên màn hình. Giữ status và message của server.
 */
export class ApiError extends Error {
  status: number
  data: unknown
  constructor(status: number, message: string, data: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

// JA: ★CSRFトークンをメモリに保持する。以前はdocument.cookieからcsrftoken Cookie
//     を直接読んでいたが、フロント(vercel.app等)とバックエンド(onrender.com等)が
//     別ドメインだと、そのCookieはブラウザが自動送信こそすれ、JS(document.cookie)
//     からは同一オリジン制限で一切読めない(実際に本番で「X-Csrftoken header has
//     incorrect length」= 常に空文字を送っていたことが原因のCSRF 403で発覚した)。
//     そこでCookieを読む代わりに、バックエンドがレスポンス本文でも配布している
//     csrfToken(CsrfView/LoginView/SignupView参照)をここに保持し、それを使う。
//     ローカル開発(同一オリジン)でもこの経路で問題なく動く。
// VI: ★Giữ CSRF token trong bộ nhớ. Trước đây đọc trực tiếp Cookie csrftoken qua
//     document.cookie, nhưng khi frontend (vercel.app...) và backend (onrender.com...)
//     khác domain, Cookie đó trình duyệt vẫn tự gửi kèm request, nhưng JS
//     (document.cookie) KHÔNG đọc được do giới hạn same-origin (thực tế phát hiện ở
//     production qua lỗi CSRF 403 "X-Csrftoken header has incorrect length" = luôn
//     gửi chuỗi rỗng). Nên thay vì đọc Cookie, giữ lại csrfToken mà backend cũng phát
//     qua body response (xem CsrfView/LoginView/SignupView) rồi dùng giá trị đó.
//     Cách này vẫn chạy tốt ở local dev (cùng origin).
let csrfToken = ''

export function setCsrfToken(token: string): void {
  csrfToken = token
}

// JA: 変更系メソッドは CSRF トークンが必要。
// VI: Các method thay đổi dữ liệu cần CSRF token.
const CSRF_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

type RequestOptions = {
  method?: string
  // JA: JSON にして送るボディ。VI: Body sẽ được JSON hóa để gửi.
  body?: unknown
  signal?: AbortSignal
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()

  const headers: Record<string, string> = {}
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (CSRF_METHODS.has(method)) headers['X-CSRFToken'] = csrfToken

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    // JA: Cookie を必ず送る（セッション認証のため）。
    // VI: Luôn gửi Cookie (cho session auth).
    credentials: 'include',
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  })

  // JA: 401 = 未認証。ログイン画面へ飛ばし、以降の処理は止める。
  // VI: 401 = chưa xác thực. Chuyển về trang đăng nhập và dừng xử lý.
  if (res.status === 401 || res.status === 403) {
    // JA: /me の 403 も未ログイン扱い。ただしログイン画面自身では無限ループを避ける。
    // VI: 403 ở /me cũng coi như chưa đăng nhập. Tránh vòng lặp vô hạn ngay trên trang login.
    if (res.status === 401 && window.location.pathname !== LOGIN_PATH) {
      window.location.assign(LOGIN_PATH)
    }
  }

  // JA: 204 No Content はボディ無し。VI: 204 No Content không có body.
  if (res.status === 204) return undefined as T

  const data = await res.json().catch(() => null)

  if (!res.ok) {
    // JA: サーバの {detail: ...} かフィールドエラーからメッセージを取り出す。
    // VI: Lấy message từ {detail: ...} của server hoặc từ lỗi theo trường.
    const message =
      (data && typeof data === 'object' && 'detail' in data && String((data as { detail: unknown }).detail)) ||
      requestFailedMessage(res.status)
    throw new ApiError(res.status, message, data)
  }

  return data as T
}

/**
 * JA: 各 feature はこの api を使う。fetch を直接触らないこと。
 * VI: Mỗi feature dùng api này. Không chạm fetch trực tiếp.
 */
export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { method: 'GET', signal }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
